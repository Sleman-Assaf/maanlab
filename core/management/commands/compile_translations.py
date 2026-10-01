"""
Compile locale/*/LC_MESSAGES/*.po files to .mo without GNU gettext.

Django's `compilemessages` needs the `msgfmt` binary, which is often missing
on Windows. This command is a small pure-Python equivalent. If GNU gettext
is installed, `python manage.py compilemessages` works as well.
"""
import ast
import struct
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def _unquote(fragment: str) -> str:
    return ast.literal_eval(fragment)


def parse_po(path: Path) -> dict:
    """Return {msgid(or ctx\\x04msgid[\\x00plural]): msgstr(\\x00-joined for plurals)}."""
    entries: dict[str, str] = {}
    ctx = msgid = plural = None
    strs: dict[int, str] = {}
    section = None
    fuzzy = False

    def flush():
        nonlocal ctx, msgid, plural, strs, fuzzy
        if msgid is not None and not (fuzzy and msgid):
            key = msgid if plural is None else f"{msgid}\x00{plural}"
            if ctx is not None:
                key = f"{ctx}\x04{key}"
            if plural is None:
                value = strs.get(0, "")
            else:
                value = "\x00".join(strs[i] for i in sorted(strs))
            if value or not msgid:
                entries[key] = value
        ctx = msgid = plural = None
        strs = {}
        fuzzy = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#,") and "fuzzy" in line:
            flush()
            fuzzy = True
            continue
        if line.startswith("#"):
            continue
        if line.startswith("msgctxt "):
            if msgid is not None:
                flush()
            ctx = _unquote(line[8:])
            section = "ctx"
        elif line.startswith("msgid_plural "):
            plural = _unquote(line[13:])
            section = "plural"
        elif line.startswith("msgid "):
            if msgid is not None:
                keep_fuzzy = fuzzy
                flush()
                fuzzy = keep_fuzzy
            msgid = _unquote(line[6:])
            section = "id"
        elif line.startswith("msgstr["):
            index = int(line[7 : line.index("]")])
            strs[index] = _unquote(line[line.index("]") + 1 :].strip())
            section = ("str", index)
        elif line.startswith("msgstr "):
            strs[0] = _unquote(line[7:])
            section = ("str", 0)
        elif line.startswith('"'):
            text = _unquote(line)
            if section == "ctx":
                ctx += text
            elif section == "id":
                msgid += text
            elif section == "plural":
                plural += text
            elif isinstance(section, tuple):
                strs[section[1]] += text
    flush()
    return entries


def write_mo(entries: dict, path: Path) -> None:
    keys = sorted(entries)
    ids = b""
    strs = b""
    offsets = []
    for key in keys:
        k = key.encode("utf-8")
        v = entries[key].encode("utf-8")
        offsets.append((len(ids), len(k), len(strs), len(v)))
        ids += k + b"\x00"
        strs += v + b"\x00"
    count = len(keys)
    key_start = 7 * 4 + 16 * count
    value_start = key_start + len(ids)
    key_table = []
    value_table = []
    for o_id, l_id, o_str, l_str in offsets:
        key_table += [l_id, o_id + key_start]
        value_table += [l_str, o_str + value_start]
    header = struct.pack("Iiiiiii", 0x950412DE, 0, count, 7 * 4, 7 * 4 + count * 8, 0, 0)
    data = header + struct.pack(f"{len(key_table)}i", *key_table) + struct.pack(f"{len(value_table)}i", *value_table)
    path.write_bytes(data + ids + strs)


class Command(BaseCommand):
    help = "Compile .po translation catalogs to .mo (pure Python, no gettext needed)."

    def handle(self, *args, **options):
        compiled = 0
        for locale_dir in settings.LOCALE_PATHS:
            for po in Path(locale_dir).rglob("*.po"):
                entries = parse_po(po)
                write_mo(entries, po.with_suffix(".mo"))
                compiled += 1
                self.stdout.write(f"  {po.relative_to(settings.BASE_DIR)}  ({len(entries) - 1} strings)")
        self.stdout.write(self.style.SUCCESS(f"Compiled {compiled} catalog(s)."))
