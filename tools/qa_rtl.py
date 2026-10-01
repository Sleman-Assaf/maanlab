"""
Arabic/RTL diagnostics (dev tool): untranslated Latin text on /ar/ pages and
animation state comparison EN vs AR after a slow scroll.

    python tools/qa_rtl.py http://127.0.0.1:8010 [width]
"""
import json
import sys

from playwright.sync_api import sync_playwright

LATIN_JS = r"""
() => {
  const allowed = /^(MAAN LAB|EN|AR|REC|2\.39 : 1|English|Excel|PDF|Django|WhatsApp|SEO|API|UX|SMS|AI|PLACEHOLDER.*|hello@.*|.*°.*|[\d\s:.,()\/·+%\-—]+)$/;
  const out = new Set();
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, t = n.textContent.trim();
    if (!t || !/[A-Za-z]/.test(t)) continue;
    const el = n.parentElement;
    if (!el || el.closest('script,style,svg,[aria-hidden="true"] .odo, .hp-field')) continue;
    if (allowed.test(t)) continue;
    out.add(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]}: ${t.slice(0, 70)}`);
  }
  const attrs = [...document.querySelectorAll('[aria-label],[placeholder],[title],[alt],[data-label-play],[data-label-pause],[data-status-template],[data-sending-label],[data-label-open]')]
    .flatMap(e => ['aria-label','placeholder','title','alt','data-label-play','data-label-pause','data-status-template','data-sending-label','data-label-open','data-label-close']
      .map(a => e.getAttribute(a)).filter(v => v && /[A-Za-z]{3,}/.test(v) && !/^(MAAN LAB|English|EN|AR)/.test(v) && !/[؀-ۿ]/.test(v)));
  return {text: [...out], attrs: [...new Set(attrs)]};
}
"""

STATE_JS = r"""
() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.height > 0; };
  const reveals = [...document.querySelectorAll('[data-reveal]')].filter(vis);
  const stuck = reveals.filter(e => !e.classList.contains('is-in') || getComputedStyle(e).opacity !== '1');
  const splits = [...document.querySelectorAll('[data-split]')];
  const splitPieces = splits.map(s => s.querySelectorAll('.split-word,.split-char').length);
  const pieceOpacity = [...document.querySelectorAll('.split-word,.split-char')].filter(e => parseFloat(getComputedStyle(e).opacity) < 0.99).length;
  const shutters = [...document.querySelectorAll('[data-shutter], .hero-feature__media.shutter')].filter(vis);
  const shutNotIn = shutters.filter(e => !e.classList.contains('is-in')).map(e => e.className.slice(0, 40));
  const counters = [...document.querySelectorAll('[data-counter]')].map(c => c.getAttribute('aria-label') + '→' +
      [...c.querySelectorAll('.odo__strip')].map(s => getComputedStyle(s).transform).join('|'));
  const hero = ['[data-hero-object]','[data-hero-in="title"]','[data-hero-stats]','.site-header'].map(s => {
      const e = document.querySelector(s); return e ? `${s}:${getComputedStyle(e).opacity}` : s + ':none'; });
  return {
    fallback: document.documentElement.classList.contains('anim-fallback'),
    ready: window.__maanReady === true,
    lenis: document.documentElement.classList.contains('has-lenis'),
    revealsTotal: reveals.length, revealsStuck: stuck.slice(0, 8).map(e => (e.className || e.tagName) + ' ' + e.textContent.trim().slice(0, 30)),
    splitHeadings: splits.length, splitNotDone: splits.filter(s => !s.classList.contains('is-split')).length,
    splitPieces, pieceOpacityBelow1: pieceOpacity,
    shutters: shutters.length, shutNotIn,
    counters, hero,
    servicesStory: document.querySelector('.services')?.classList.contains('is-story'),
    activeService: [...document.querySelectorAll('[data-svc]')].findIndex(s => s.classList.contains('is-active')),
  };
}
"""


def main(base, width=1440):
    width = int(width)
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for lang in ("en", "ar"):
            ctx = browser.new_context(viewport={"width": width, "height": 900})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: m.type in ("error", "warning") and errors.append(m.text))
            page.goto(f"{base}/{lang}/", wait_until="networkidle")
            page.wait_for_timeout(3500)
            total = page.evaluate("document.documentElement.scrollHeight")
            y = 0
            while y < total:
                y += 300
                page.mouse.wheel(0, 300)
                page.wait_for_timeout(160)
                total = page.evaluate("document.documentElement.scrollHeight")
            page.wait_for_timeout(3000)
            state = page.evaluate(STATE_JS)
            state["errors"] = errors
            # services storyteller progression (desktop)
            if width >= 1024:
                seq = []
                page.evaluate("window.scrollTo(0,0)")
                page.wait_for_timeout(500)
                story = page.evaluate("(() => { const s = document.querySelector('[data-services]'); let t=0,n=s; while(n){t+=n.offsetTop;n=n.offsetParent;} return [t, s.offsetHeight]; })()")
                for frac in (0.1, 0.35, 0.6, 0.9):
                    page.evaluate(f"window.scrollTo(0, {story[0]} + ({story[1]} - innerHeight) * {frac})")
                    page.wait_for_timeout(1500)
                    seq.append(page.evaluate("[...document.querySelectorAll('[data-svc]')].findIndex(s => s.classList.contains('is-active'))"))
                state["storySequence"] = seq
            if lang == "ar":
                state["latin"] = page.evaluate(LATIN_JS)
                page.goto(f"{base}/ar/projects/sandstone-product-film/", wait_until="networkidle")
                page.wait_for_timeout(1500)
                state["latinDetail"] = page.evaluate(LATIN_JS)
            report[lang] = state
            ctx.close()
        browser.close()
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:])
