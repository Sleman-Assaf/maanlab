"""
Hero workflow QA (dev tool): geometry at every breakpoint, draw progression,
ambient data dot, reduced motion, RTL, console errors.

    python tools/qa_hero_workflow.py http://127.0.0.1:8010 out_dir
"""
import json
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

SIZES = [(1440, 900), (1280, 800), (1024, 768), (768, 1024), (430, 932), (390, 844)]

GEOMETRY_JS = r"""
() => {
  const svg = document.querySelector('[data-wf]');
  const r = svg.getBoundingClientRect();
  const col = document.querySelector('.hero__visual').getBoundingClientRect();
  const h1 = document.querySelector('.hero__title').getBoundingClientRect();
  const lead = document.querySelector('.hero__lead').getBoundingClientRect();
  const stats = document.querySelector('[data-hero-stats]').getBoundingClientRect();
  const overlap = (a, b) => !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
  const drawn = [...svg.querySelectorAll('.wf-draw')].filter(p => getComputedStyle(p).display !== 'none' && getComputedStyle(p.closest('.wf-full,.wf-compact') || p).display !== 'none');
  const undrawn = drawn.filter(p => parseFloat(getComputedStyle(p).strokeDashoffset) > 0.01 || +getComputedStyle(p).opacity < 0.99).length;
  const sw = parseFloat(getComputedStyle(svg.querySelector('.wf-draw')).strokeWidth);
  return {
    svg: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    widthOfColumn: +(r.width / col.width).toFixed(2),
    heightOfColumnAboveStats: col.height ? +(r.height / Math.max(1, (stats.top - col.top))).toFixed(2) : null,
    insideColumn: r.left >= col.left - 1 && r.right <= col.right + 1,
    overlapsHeadline: overlap(r, h1), overlapsLead: overlap(r, lead), overlapsStats: overlap(r, stats),
    screenStrokePx: +(sw * r.height / 760).toFixed(2),
    visiblePaths: drawn.length, undrawn,
    mode: getComputedStyle(svg.querySelector('.wf-full')).display === 'none' ? 'compact' : 'full',
    hscroll: document.documentElement.scrollWidth > document.documentElement.clientWidth,
    dir: document.documentElement.dir,
  };
}
"""


def run(base, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for lang in ("en", "ar"):
            for w, h in SIZES:
                key = f"{lang}-{w}"
                ctx = browser.new_context(viewport={"width": w, "height": h}, has_touch=w < 810, is_mobile=w < 810)
                page = ctx.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on("console", lambda m: m.type in ("error", "warning") and errors.append(m.text))
                page.goto(f"{base}/{lang}/", wait_until="networkidle")
                # Draw progression (desktop EN/AR only)
                if w == 1440:
                    frames = []
                    for i, t in enumerate([700, 500, 500, 500, 500, 700, 900]):
                        page.wait_for_timeout(t)
                        path = out / f"{key}-draw-{i}.png"
                        box = page.evaluate("(() => { const r = document.querySelector('.hero__visual').getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })()")
                        page.screenshot(path=str(path), clip={"x": max(0, box[0] - 20), "y": 60, "width": min(w - box[0] + 20, 620), "height": 800})
                        frames.append(path)
                    ims = [Image.open(f) for f in frames]
                    sheet = Image.new("RGB", (sum(i.width for i in ims), ims[0].height))
                    x = 0
                    for im in ims:
                        sheet.paste(im, (x, 0))
                        x += im.width
                    sheet.resize((sheet.width // 2, sheet.height // 2)).save(out / f"{key}-draw-sheet.png")
                else:
                    page.wait_for_timeout(4500)
                geo = page.evaluate(GEOMETRY_JS)
                # Ambient dot moves?
                d1 = page.evaluate("document.querySelector('[data-wf-dot]').getAttribute('transform')")
                page.wait_for_timeout(1200)
                d2 = page.evaluate("document.querySelector('[data-wf-dot]').getAttribute('transform')")
                geo["dotMoving"] = d1 != d2
                geo["dotOpacity"] = page.evaluate("getComputedStyle(document.querySelector('[data-wf-dot]')).opacity")
                page.screenshot(path=str(out / f"{key}-hero.png"))
                geo["errors"] = errors
                report[key] = geo
                ctx.close()
        # Reduced motion: full sketch immediately, no dot
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = ctx.new_page()
        page.goto(f"{base}/en/", wait_until="networkidle")
        page.wait_for_timeout(300)
        report["reduced-motion"] = page.evaluate(GEOMETRY_JS) | {
            "dotOpacity": page.evaluate("getComputedStyle(document.querySelector('[data-wf-dot]')).opacity")
        }
        page.screenshot(path=str(out / "reduced-hero.png"))
        ctx.close()
        browser.close()
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
