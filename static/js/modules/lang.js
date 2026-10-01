/*
 * Language switch: the server already links to the same page in the other
 * language (/en/… ↔ /ar/…). Here we keep the query string and hash too, and
 * remember the choice for the root "/" redirect.
 */
export function initLanguageSwitch() {
  document.querySelectorAll("[data-lang-link]").forEach((link) => {
    link.addEventListener("click", () => {
      const code = link.dataset.langLink;
      document.cookie = `django_language=${code}; path=/; max-age=31536000; SameSite=Lax`;
      const url = new URL(link.href, window.location.href);
      if (!url.search) url.search = window.location.search;
      if (!url.hash) url.hash = window.location.hash;
      link.href = url.toString();
    });
  });
}
