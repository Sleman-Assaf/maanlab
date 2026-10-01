"""
Copy QA (dev tool): no English leaking into /ar/, no Arabic leaking into /en/,
across pages and form states (validation errors, success).

    python tools/qa_copy.py http://127.0.0.1:8010
"""
import json
import re
import sys

from playwright.sync_api import sync_playwright

TEXT_JS = r"""
() => {
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const n = walker.currentNode, t = n.textContent.trim(), el = n.parentElement;
    if (!t || !el || el.closest('script,style,.hp-field,[hidden]')) continue;
    out.push(t);
  }
  const attrs = [...document.querySelectorAll('[aria-label],[placeholder],[alt],[title],[data-label-play],[data-label-pause],[data-status-template],[data-sending-label],[data-label-open],[data-label-close],[data-label-view]')]
    .flatMap(e => ['aria-label','placeholder','alt','title','data-label-play','data-label-pause','data-status-template','data-sending-label','data-label-open','data-label-close','data-label-view'].map(a => e.getAttribute(a)).filter(Boolean));
  return {texts: out, attrs, title: document.title, desc: document.querySelector('meta[name=description]')?.content || ''};
}
"""

# Brand/product names and technical tokens allowed in Arabic pages.
AR_ALLOWED = re.compile(
    r"^(MAAN LAB|EN|AR|REC|2\.39 : 1|English|Excel|PDF|Django|WhatsApp|SEO|API|AI|UX|SMS|Instagram|Facebook|LinkedIn|"
    r"CONTACT_EMAIL|hello@\S+|©.*|[\d\s:.,()/·+%°NE\-—]+)$"
)
ARABIC = re.compile(r"[؀-ۿ]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
EN_ALLOWED_ARABIC = {"العربية", "English · العربية"}


def check(page, lang):
    data = page.evaluate(TEXT_JS)
    issues = []
    items = data["texts"] + data["attrs"] + [data["title"], data["desc"]]
    for t in items:
        if lang == "ar":
            for word in LATIN_WORD.findall(t):
                if not AR_ALLOWED.match(word) and word not in {"MAAN", "LAB", "Excel", "AI", "API", "EN", "CONTACT", "EMAIL", "Instagram", "Facebook", "LinkedIn", "English", "hello", "maanlab", "com", "REC", "PLACEHOLDER", "SANDSTONE"}:
                    issues.append(t[:90])
                    break
        else:
            if ARABIC.search(t) and t not in EN_ALLOWED_ARABIC:
                issues.append(t[:90])
    return sorted(set(issues))


def main(base):
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        for lang in ("en", "ar"):
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            page = ctx.new_page()
            for path in ("/", "/projects/sandstone-product-film/", "/projects/from-spreadsheets-to-system/", "/nope/"):
                page.goto(f"{base}/{lang}{path}", wait_until="networkidle")
                page.wait_for_timeout(600)
                report[f"{lang}{path}"] = check(page, lang)
            # contact error state
            page.goto(f"{base}/{lang}/#contact", wait_until="networkidle")
            page.evaluate("document.querySelector('[data-contact-form]').setAttribute('novalidate','')")
            page.fill("#id_name", "A")
            page.fill("#id_email", "bad")
            page.fill("#id_phone", "call me")
            page.fill("#id_message", "hi")
            page.click("[data-submit]")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            report[f"{lang}/contact-errors"] = check(page, lang)
            report[f"{lang}/contact-errors-text"] = page.evaluate(
                "[document.querySelector('.form-errors__title')?.textContent, ...[...document.querySelectorAll('.field__error')].map(e=>e.textContent)]"
            )
            page.fill("#id_name", "Test User")
            page.fill("#id_email", "test@example.com")
            page.fill("#id_phone", "+962790000000")
            page.select_option("#id_service", "ai_video")
            page.fill("#id_message", "A proper message about the project.")
            page.click("[data-submit]")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            report[f"{lang}/contact-success"] = check(page, lang)
            report[f"{lang}/contact-success-text"] = page.evaluate(
                "document.querySelector('[data-form-success]')?.innerText.replace(/\\s+/g,' ')"
            )
            ctx.close()
        browser.close()
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
