"""
Pure-Python message extractor (fallback for `makemessages`, which needs GNU gettext).
Scans templates for {% translate %} / {% blocktranslate %} (including `context "…"`)
and Python files for _() / gettext / pgettext calls, then merges with
locale_src/translations_ar.py and writes locale/ar/LC_MESSAGES/django.po.

    python tools/extract_strings.py          # write django.po, report missing
    python tools/extract_strings.py --list   # list msgids
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TEMPLATE_RE = re.compile(
    r"""\{%\s*(?:translate|trans)\s+(["'])(?P<msg>.+?)\1(?:\s+context\s+(["'])(?P<ctx>.+?)\3)?""", re.S
)
BLOCK_RE = re.compile(
    r"""\{%\s*blocktranslate\b(?P<args>[^%]*)%\}(?P<body>.*?)\{%\s*endblocktranslate\s*%\}""", re.S
)
BLOCK_CTX_RE = re.compile(r"""context\s+(["'])(.+?)\1""")
BLOCK_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def extract() -> dict[tuple[str | None, str], set[str]]:
    """Return {(context, msgid): {source files}}."""
    found: dict[tuple[str | None, str], set[str]] = {}

    def add(ctx, msg, where):
        found.setdefault((ctx, msg), set()).add(where)

    for path in (ROOT / "templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        for m in TEMPLATE_RE.finditer(text):
            add(m.group("ctx"), m.group("msg"), rel)
        for m in BLOCK_RE.finditer(text):
            ctx = BLOCK_CTX_RE.search(m.group("args"))
            body = BLOCK_VAR_RE.sub(lambda v: f"%({v.group(1)})s", m.group("body"))
            add(ctx.group(2) if ctx else None, body, rel)

    for app in ("core", "projects", "contact", "config"):
        for path in (ROOT / app).rglob("*.py"):
            if "migrations" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                    continue
                args = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                if node.func.id in {"_", "gettext", "gettext_lazy"} and args:
                    add(None, args[0], str(path.relative_to(ROOT)))
                elif node.func.id in {"pgettext", "pgettext_lazy"} and len(args) >= 2:
                    add(args[0], args[1], str(path.relative_to(ROOT)))
    return found


def po_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def main():
    from locale_src.translations_ar import AR, AR_CONTEXT  # noqa: E402

    found = extract()
    header = (
        'msgid ""\n'
        'msgstr ""\n'
        '"Project-Id-Version: maanlab\\n"\n'
        '"Language: ar\\n"\n'
        '"MIME-Version: 1.0\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n'
        '"Plural-Forms: nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5;\\n"\n'
    )
    lines = [header]
    missing = []
    for ctx, msgid in sorted(found, key=lambda k: (k[1], k[0] or "")):
        refs = " ".join(sorted(found[(ctx, msgid)]))
        translation = AR_CONTEXT.get((ctx, msgid), "") if ctx else AR.get(msgid, "")
        if not translation:
            missing.append((ctx, msgid))
        entry = f"#: {refs}\n"
        if ctx:
            entry += f'msgctxt "{po_escape(ctx)}"\n'
        entry += f'msgid "{po_escape(msgid)}"\nmsgstr "{po_escape(translation)}"\n'
        lines.append(entry)
    out = ROOT / "locale/ar/LC_MESSAGES/django.po"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(found)} strings, {len(missing)} missing Arabic translations")
    for ctx, msgid in missing:
        print("  MISSING:", repr(msgid), f"(context: {ctx})" if ctx else "")
    used_plain = {m for c, m in found if c is None}
    used_ctx = {k for k in found if k[0] is not None}
    for u in sorted(set(AR) - used_plain):
        print("  unused:", repr(u))
    for u in sorted(set(AR_CONTEXT) - used_ctx):
        print("  unused (context):", repr(u))


if __name__ == "__main__":
    if "--list" in sys.argv:
        for ctx, msgid in sorted(extract(), key=lambda k: (k[1], k[0] or "")):
            print(repr(msgid), f"[{ctx}]" if ctx else "")
    else:
        main()
