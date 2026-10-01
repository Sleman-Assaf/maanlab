"""
Mobile QA (dev tool): runs on Chromium (Edge) and WebKit (Safari engine).

    python -m playwright install webkit      # once
    python tools/qa_mobile.py http://127.0.0.1:8010 out_dir

Checks per engine × language × width (360/390/430):
  horizontal overflow, small tap targets, tiny text, hero object near the fold,
  pins disabled on mobile, mobile menu (tap → close → scrolls to section),
  services accordion, project filter by tap, contact submission, detail page.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WIDTHS = [(360, 780), (390, 844), (430, 932)]

AUDIT_JS = r"""
() => {
  const vw = document.documentElement.clientWidth;
  const visible = (el) => {
    const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !el.closest('[inert],[hidden],.hp-field,.sr-only');
  };
  const overflow = [...document.querySelectorAll('main *, header *, footer *')]
    .filter(e => visible(e) && !e.closest('.hero__bg,.hero-object,.reel__media,.hero__shade'))
    .filter(e => { const r = e.getBoundingClientRect(); return r.right > vw + 1 || r.left < -1; })
    .slice(0, 6).map(e => `${e.tagName}.${String(e.className).slice(0,40)} ${Math.round(e.getBoundingClientRect().left)}→${Math.round(e.getBoundingClientRect().right)}`);
  const small = [...document.querySelectorAll('a[href], button, input, select, textarea, label.choice-pill')]
    .filter(visible)
    .filter(e => !e.closest('.site-footer__bottom, .footer-col, .contact__details, .site-footer__intro'))
    .map(e => ({e, r: e.getBoundingClientRect()}))
    .filter(({r}) => r.height < 40 && r.width < 40 || r.height < 32)
    .slice(0, 10).map(({e, r}) => `${e.tagName}.${String(e.className).slice(0,30)} "${(e.textContent||'').trim().slice(0,20)}" ${Math.round(r.width)}x${Math.round(r.height)}`);
  const tiny = [...document.querySelectorAll('main p, main span, main a, main li, main dt, main dd, main label, footer p, footer a')]
    .filter(visible).filter(e => e.childElementCount === 0 && e.textContent.trim())
    .filter(e => parseFloat(getComputedStyle(e).fontSize) < 10.5)
    .slice(0, 6).map(e => `${e.className || e.tagName} ${getComputedStyle(e).fontSize} "${e.textContent.trim().slice(0,20)}"`);
  const obj = document.querySelector('[data-hero-object]');
  return {
    scrollWidth: document.documentElement.scrollWidth, clientWidth: vw,
    overflow, smallTargets: small, tinyText: tiny,
    heroObjectTop: obj ? Math.round(obj.getBoundingClientRect().top) : null,
    heroPosition: getComputedStyle(document.querySelector('.hero')).position,
    aboutPosition: getComputedStyle(document.querySelector('.about')).position,
    servicesStory: document.querySelector('.services').classList.contains('is-story'),
    lenis: document.documentElement.classList.contains('has-lenis'),
  };
}
"""


def run(base, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        engines = {"chromium": p.chromium.launch(channel="msedge", headless=True), "webkit": p.webkit.launch(headless=True)}
        for engine, browser in engines.items():
            for lang in ("en", "ar"):
                for w, h in WIDTHS:
                    key = f"{engine}-{lang}-{w}"
                    ctx = browser.new_context(viewport={"width": w, "height": h}, has_touch=True,
                                              is_mobile=engine == "chromium", device_scale_factor=2)
                    page = ctx.new_page()
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
                    page.on("response", lambda r: r.status >= 400 and errors.append(f"{r.status} {r.url}"))
                    page.goto(f"{base}/{lang}/", wait_until="networkidle")
                    page.wait_for_timeout(2500)
                    # scroll through the page so everything reveals
                    total = page.evaluate("document.documentElement.scrollHeight")
                    y = 0
                    while y < total:
                        y += h // 2
                        page.evaluate(f"window.scrollTo(0,{y})")
                        page.wait_for_timeout(120)
                    page.wait_for_timeout(800)
                    page.evaluate("window.scrollTo(0,0)")
                    page.wait_for_timeout(600)
                    result = page.evaluate(AUDIT_JS)
                    if w == 390:
                        page.screenshot(path=str(out / f"{key}-full.png"), full_page=True)

                    # Menu: open, tap "Projects", expect closed + scrolled to #projects
                    page.tap("[data-menu-toggle]")
                    page.wait_for_timeout(700)
                    menu_open = page.evaluate("document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded')")
                    if w == 390:
                        page.screenshot(path=str(out / f"{key}-menu.png"))
                    page.tap(".site-menu__list li:nth-child(3) a")
                    page.wait_for_timeout(1800)
                    result["menu"] = {
                        "opened": menu_open,
                        "closedAfterTap": page.evaluate("document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded')"),
                        "projectsTop": page.evaluate("Math.round(document.querySelector('#projects').getBoundingClientRect().top)"),
                        "scrollLocked": page.evaluate("document.documentElement.classList.contains('scroll-locked')"),
                    }

                    # Project filter by tap
                    page.tap("[data-filter=ai_automation]")
                    page.wait_for_timeout(1200)
                    result["filter"] = page.evaluate(
                        "[...document.querySelectorAll('.project-grid__item')].filter(e=>!e.hidden).map(e=>e.dataset.category)"
                    )
                    page.tap("[data-filter=all]")
                    page.wait_for_timeout(900)
                    result["videosPlaying"] = page.evaluate("[...document.querySelectorAll('video')].filter(v=>!v.paused).length")

                    # Services accordion
                    page.evaluate("document.querySelector('#services').scrollIntoView()")
                    page.wait_for_timeout(500)
                    page.tap("[data-svc]:nth-child(3) [data-svc-btn]")
                    page.wait_for_timeout(900)
                    result["accordion"] = page.evaluate(
                        "[...document.querySelectorAll('[data-svc]')].map(s=>s.classList.contains('is-active')?1:0).join('')"
                    )
                    if w == 390:
                        page.evaluate("document.querySelector('[data-svc]:nth-child(3)').scrollIntoView({block:'start'})")
                        page.wait_for_timeout(1200)
                        page.screenshot(path=str(out / f"{key}-accordion.png"))
                    result["errors"] = errors
                    report[key] = result
                    ctx.close()

            # Contact submission + detail page (390 only)
            for lang in ("en", "ar"):
                ctx = browser.new_context(viewport={"width": 390, "height": 844}, has_touch=True, device_scale_factor=2)
                page = ctx.new_page()
                page.goto(f"{base}/{lang}/#contact", wait_until="networkidle")
                page.wait_for_timeout(1200)
                page.fill("#id_name", "Test Mobile")
                page.fill("#id_email", "mobile@example.com")
                page.select_option("#id_service", "web_development")
                page.fill("#id_message", "Testing the contact form from a phone viewport.")
                page.locator("[data-submit]").scroll_into_view_if_needed()
                page.tap("[data-submit]")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1200)
                page.screenshot(path=str(out / f"{engine}-{lang}-contact-success.png"))
                success = page.evaluate("!!document.querySelector('[data-form-success]')")
                page.goto(f"{base}/{lang}/projects/night-market-campaign/", wait_until="networkidle")
                page.wait_for_timeout(1800)
                page.screenshot(path=str(out / f"{engine}-{lang}-detail.png"), full_page=True)
                detail = page.evaluate(
                    "({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,"
                    " video: !!document.querySelector('.project-cover video')})"
                )
                report[f"{engine}-{lang}-flows"] = {"contactSuccess": success, "detail": detail}
                ctx.close()
            browser.close()
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
