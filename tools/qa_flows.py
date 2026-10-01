"""
Interaction QA (dev tool): mobile menu, project detail (EN/AR), contact form
(invalid + valid), reduced motion, 404, language switch, keyboard filter.

    python tools/qa_flows.py http://127.0.0.1:8010 out_dir
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main(base, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # --- Mobile menu (EN + AR) -------------------------------------------
        for lang in ("en", "ar"):
            ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
            page = ctx.new_page()
            page.goto(f"{base}/{lang}/", wait_until="networkidle")
            page.wait_for_timeout(1500)
            toggle = page.locator("[data-menu-toggle]")
            toggle.click()
            page.wait_for_timeout(900)
            page.screenshot(path=str(out / f"menu-{lang}-open.png"))
            state = page.evaluate(
                "({expanded: document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded'),"
                " inert: document.querySelector('#site-menu').hasAttribute('inert'),"
                " focused: document.activeElement.textContent.trim().slice(0,20),"
                " locked: document.documentElement.classList.contains('scroll-locked')})"
            )
            page.keyboard.press("Escape")
            page.wait_for_timeout(700)
            state["after_escape"] = page.evaluate("document.querySelector('[data-menu-toggle]').getAttribute('aria-expanded')")
            results[f"menu-{lang}"] = state
            ctx.close()

        # --- Project detail pages --------------------------------------------
        for lang, (w, h) in [("en", (1440, 900)), ("ar", (1440, 900)), ("en", (390, 844)), ("ar", (390, 844))]:
            ctx = browser.new_context(viewport={"width": w, "height": h})
            page = ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: m.type == "error" and errors.append(m.text))
            resp = page.goto(f"{base}/{lang}/projects/sandstone-product-film/", wait_until="networkidle")
            page.wait_for_timeout(2500)
            page.screenshot(path=str(out / f"detail-{lang}-{w}-top.png"))
            page.mouse.wheel(0, h * 1.2)
            page.wait_for_timeout(1800)
            page.screenshot(path=str(out / f"detail-{lang}-{w}-body.png"))
            results[f"detail-{lang}-{w}"] = {
                "status": resp.status,
                "errors": errors,
                "title": page.title(),
                "dir": page.evaluate("document.documentElement.dir"),
                "hreflang": page.evaluate("[...document.querySelectorAll('link[hreflang]')].map(l=>l.hreflang+'='+l.href)"),
            }
            ctx.close()

        # --- Contact: invalid then valid submission --------------------------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(f"{base}/en/#contact", wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.evaluate("document.querySelector('[data-contact-form]').setAttribute('novalidate','')")
        page.fill("#id_name", "A")
        page.fill("#id_email", "not-an-email")
        page.fill("#id_message", "short")
        page.click("[data-submit]")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(out / "contact-invalid.png"))
        results["contact-invalid"] = page.evaluate(
            "({url: location.href, errors: [...document.querySelectorAll('.field__error')].map(e=>e.textContent),"
            " summary: !!document.querySelector('[data-form-errors]'), focused: document.activeElement.className,"
            " invalidAttr: document.querySelector('#id_email').getAttribute('aria-invalid'),"
            " describedby: document.querySelector('#id_email').getAttribute('aria-describedby'),"
            " keptName: document.querySelector('#id_name').value})"
        )
        page.fill("#id_name", "Layla Haddad")
        page.fill("#id_email", "layla@example.com")
        page.fill("#id_phone", "+962 79 000 0000")
        page.fill("#id_company", "Example Co.")
        page.select_option("#id_service", "ai_video")
        page.check("input[name=preferred_language][value=ar]")
        page.fill("#id_message", "We need a 30-second AI product film for a new launch in November.")
        page.click("[data-submit]")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(out / "contact-success.png"))
        results["contact-valid"] = page.evaluate(
            "({url: location.href, success: document.querySelector('[data-form-success]')?.textContent.trim().replace(/\\s+/g,' ')})"
        )
        ctx.close()

        # --- Reduced motion -----------------------------------------------------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page = ctx.new_page()
        page.goto(f"{base}/en/", wait_until="networkidle")
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / "reduced-hero.png"))
        page.evaluate("window.scrollTo(0, document.querySelector('#projects').offsetTop)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / "reduced-projects.png"))
        results["reduced"] = page.evaluate(
            "({rm: document.documentElement.classList.contains('rm'), lenis: document.documentElement.classList.contains('has-lenis'),"
            " hidden: [...document.querySelectorAll('[data-reveal]')].filter(e=>getComputedStyle(e).opacity==='0').length,"
            " split: document.querySelectorAll('.split-char').length,"
            " autoplaying: [...document.querySelectorAll('video')].filter(v=>!v.paused).length})"
        )
        ctx.close()

        # --- No-JS rendering ------------------------------------------------------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900}, java_script_enabled=False)
        page = ctx.new_page()
        page.goto(f"{base}/en/?category=web_development", wait_until="networkidle")
        page.evaluate if False else None
        page.screenshot(path=str(out / "nojs-hero.png"))
        page.locator("#projects").scroll_into_view_if_needed()
        page.screenshot(path=str(out / "nojs-projects.png"))
        ctx.close()

        # --- 404 + language switch + keyboard filter -----------------------------
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        resp = page.goto(f"{base}/en/does-not-exist/", wait_until="networkidle")
        results["404"] = resp.status
        page.goto(f"{base}/en/projects/clinic-booking-web-app/", wait_until="networkidle")
        page.click(".lang-switch--header [data-lang-link=ar]")
        page.wait_for_load_state("networkidle")
        results["lang-switch"] = {"url": page.url, "dir": page.evaluate("document.documentElement.dir")}
        page.goto(f"{base}/en/#projects", wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.focus("[data-filter=web_development]")
        page.keyboard.press("Enter")
        page.wait_for_timeout(1200)
        results["keyboard-filter"] = page.evaluate(
            "({visible: [...document.querySelectorAll('.project-grid__item')].filter(e=>!e.hidden).length,"
            " url: location.search, status: document.querySelector('[data-filter-status]').textContent})"
        )
        ctx.close()
        browser.close()
    print(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
