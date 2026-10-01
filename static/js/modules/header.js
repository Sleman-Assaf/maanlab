/* Header: scrolled glass state, light/dark theme per section, active link, mobile menu. */
import { EASE, hasGSAP, reduced } from "./env.js";
import { lockScroll } from "./smooth-scroll.js";

export function initHeader() {
  const header = document.querySelector("[data-header]");
  if (!header) return;

  const themed = [...document.querySelectorAll("[data-nav-theme]")];
  const sections = [...document.querySelectorAll("[data-nav-section]")];
  const links = [...header.querySelectorAll("[data-nav-link]")];

  /* --- Scroll state ------------------------------------------------------ */
  let ticking = false;
  const update = () => {
    ticking = false;
    const probe = header.offsetHeight / 2;
    header.classList.toggle("is-scrolled", window.scrollY > 24);

    // Later sections stack above earlier ones (curtains), so the last match wins.
    let theme = "dark";
    for (const el of themed) {
      const r = el.getBoundingClientRect();
      if (r.top <= probe && r.bottom >= probe) theme = el.dataset.navTheme;
    }
    if (!header.classList.contains("is-open")) header.dataset.theme = theme;

    if (links.length && sections.length) {
      const line = window.innerHeight * 0.4;
      let current = "top";
      for (const el of sections) {
        if (el.getBoundingClientRect().top <= line) current = el.dataset.navSection;
      }
      links.forEach((link) => {
        const active = link.dataset.navLink === current;
        link.classList.toggle("is-active", active);
        if (active) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }
  };
  const requestUpdate = () => {
    if (!ticking) {
      ticking = true;
      window.requestAnimationFrame(update);
    }
  };
  window.addEventListener("scroll", requestUpdate, { passive: true });
  window.addEventListener("resize", requestUpdate);
  update();

  /* --- Mobile menu ------------------------------------------------------- */
  const toggle = header.querySelector("[data-menu-toggle]");
  const menu = header.querySelector("[data-menu]");
  if (!toggle || !menu) return;
  const label = toggle.querySelector("[data-menu-label]");
  const menuLinks = [...menu.querySelectorAll("[data-menu-link], .lang-switch__link")];
  let open = false;

  const focusables = () =>
    [toggle, ...menu.querySelectorAll("a[href], button:not([disabled])")].filter((el) => el.offsetParent !== null);

  const onKeydown = (event) => {
    if (event.key === "Escape") {
      setOpen(false);
      toggle.focus();
    } else if (event.key === "Tab") {
      const items = focusables();
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  };

  function setOpen(next) {
    if (next === open) return;
    open = next;
    header.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    if (label) label.textContent = open ? toggle.dataset.labelClose : toggle.dataset.labelOpen;
    menu.toggleAttribute("inert", !open);
    menu.setAttribute("aria-hidden", String(!open));
    lockScroll(open);

    if (open) {
      header.dataset.theme = "dark";
      document.addEventListener("keydown", onKeydown);
      if (hasGSAP() && !reduced()) {
        window.gsap.fromTo(
          menu.querySelectorAll(".site-menu__list li, .site-menu__foot > *"),
          { opacity: 0, y: 24 },
          { opacity: 1, y: 0, duration: 0.6, ease: EASE.io, stagger: 0.05, delay: 0.12, overwrite: true }
        );
      }
      window.setTimeout(() => menuLinks[0]?.focus({ preventScroll: true }), 80);
    } else {
      document.removeEventListener("keydown", onKeydown);
      requestUpdate();
    }
  }

  toggle.addEventListener("click", () => setOpen(!open));
  menuLinks.forEach((link) => link.addEventListener("click", () => setOpen(false)));
  window.matchMedia("(min-width: 1024px)").addEventListener?.("change", (e) => e.matches && setOpen(false));
}
