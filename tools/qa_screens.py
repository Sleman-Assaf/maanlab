"""
Visual + runtime QA (dev tool). Requires `pip install playwright` and Edge/Chrome.

    python tools/qa_screens.py http://127.0.0.1:8010 out_dir [--only en-1440]

For every language × viewport it:
  • scrolls through the page slowly (so scroll-triggered reveals fire),
  • captures screenshots at each section,
  • reports console errors, failed requests (404s) and horizontal overflow.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORTS = {"1440": (1440, 900), "1280": (1280, 800), "1024": (1024, 768), "768": (768, 1024), "430": (430, 932), "390": (390, 844)}
SECTIONS = ["#top", "#services", ".reel", "#projects", "#about", "#contact", "#site-footer"]


def run(base, out, only=None, reduced=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for lang in ("en", "ar"):
            for name, (w, h) in VIEWPORTS.items():
                key = f"{lang}-{name}"
                if only and key not in only:
                    continue
                ctx = browser.new_context(
                    viewport={"width": w, "height": h},
                    device_scale_factor=1,
                    reduced_motion="reduce" if reduced else "no-preference",
                    has_touch=w < 810,
                    is_mobile=w < 810,
                )
                page = ctx.new_page()
                errors, failed = [], []
                page.on("console", lambda m: m.type == "error" and errors.append(m.text))
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("response", lambda r: r.status >= 400 and failed.append(f"{r.status} {r.url}"))
                page.goto(f"{base}/{lang}/", wait_until="networkidle")
                page.wait_for_timeout(3000)
                page.screenshot(path=str(out / f"{key}-00-hero.png"))
                # slow scroll to trigger everything
                height = page.evaluate("document.documentElement.scrollHeight")
                y = 0
                while y < height:
                    y += int(h * 0.5)
                    page.mouse.wheel(0, int(h * 0.5))
                    page.wait_for_timeout(220)
                    height = page.evaluate("document.documentElement.scrollHeight")
                overflow = page.evaluate(
                    "(() => { const w = document.documentElement.clientWidth; return [...document.querySelectorAll('body *')]"
                    ".filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.right > w + 1 || r.left < -1) && getComputedStyle(e).position !== 'fixed'; })"
                    ".slice(0, 8).map(e => e.tagName + '.' + (e.className && e.className.baseVal === undefined ? e.className : '') + ' ' + Math.round(e.getBoundingClientRect().left) + '→' + Math.round(e.getBoundingClientRect().right)); })()"
                )
                scroll_w = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                for i, sel in enumerate(SECTIONS, start=1):
                    exists = page.evaluate(f"!!document.querySelector('{sel}')")
                    if not exists:
                        continue
                    page.evaluate(
                        "(sel) => { const el = document.querySelector(sel); let t = 0, n = el; "
                        "while (n) { t += n.offsetTop; n = n.offsetParent; } window.scrollTo(0, t + 40); }",
                        sel,
                    )
                    page.wait_for_timeout(1600)
                    page.screenshot(path=str(out / f"{key}-{i:02d}-{sel.strip('#.')}.png"))
                report[key] = {"errors": errors, "failed": failed, "horizontal_scroll": scroll_w, "overflowing": overflow}
                ctx.close()
        browser.close()
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        args = [a for a in args if a not in only]
    run(args[0], args[1], only, reduced="--reduced" in sys.argv)
