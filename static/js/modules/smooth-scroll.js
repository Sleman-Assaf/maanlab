/* Lenis smooth scroll — ORYN settings: lerp ≈ 0.11, ≥810px only, off for reduced motion. */
import { hasGSAP, html, reduced, onReducedChange } from "./env.js";

let lenis = null;
const desktop = window.matchMedia("(min-width: 810px)");

const raf = (time) => {
  if (lenis) lenis.raf(time * 1000);
};

function create() {
  if (lenis || reduced() || !desktop.matches || !window.Lenis) return;
  const gsapDriven = hasGSAP();
  lenis = new window.Lenis({
    lerp: 0.11,
    wheelMultiplier: 1,
    syncTouch: false,
    autoRaf: !gsapDriven,
    anchors: false, // anchors are handled in scrollToTarget() so sticky sections resolve correctly
  });
  if (gsapDriven) {
    lenis.on("scroll", window.ScrollTrigger.update);
    window.gsap.ticker.add(raf);
    window.gsap.ticker.lagSmoothing(0);
  }
  html.classList.add("has-lenis");
}

function destroy() {
  if (!lenis) return;
  if (hasGSAP()) window.gsap.ticker.remove(raf);
  lenis.destroy();
  lenis = null;
  html.classList.remove("has-lenis");
}

export function getLenis() {
  return lenis;
}

/* Document offset of an element, ignoring sticky/transform offsets. */
function documentTop(el) {
  let top = 0;
  let node = el;
  while (node) {
    top += node.offsetTop;
    node = node.offsetParent;
  }
  return top;
}

export function scrollToY(y, { immediate = false } = {}) {
  const target = Math.max(0, y);
  if (lenis) {
    lenis.scrollTo(target, { duration: immediate ? 0 : 1.3, immediate });
  } else {
    window.scrollTo({ top: target, behavior: immediate || reduced() ? "auto" : "smooth" });
  }
}

export function scrollToTarget(el, options = {}) {
  if (!el) return;
  const offset = options.offset ?? 0;
  scrollToY(documentTop(el) - offset, options);
}

export function lockScroll(locked) {
  if (lenis) (locked ? lenis.stop() : lenis.start());
  html.classList.toggle("scroll-locked", locked);
}

function bindAnchors() {
  document.addEventListener("click", (event) => {
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey) return;
    const link = event.target.closest("a[href*='#']");
    if (!link) return;
    const url = new URL(link.href, window.location.href);
    if (url.pathname !== window.location.pathname || url.search !== window.location.search || !url.hash) return;
    const id = decodeURIComponent(url.hash.slice(1));
    const target = id === "top" ? document.body : document.getElementById(id);
    if (!target) return;
    event.preventDefault();
    if (id === "top") scrollToY(0);
    else scrollToTarget(target);
    history.replaceState(null, "", url.hash);
    const focusTarget = id === "top" ? document.getElementById("main") : target;
    window.setTimeout(() => focusTarget?.focus?.({ preventScroll: true }), 900);
  });
}

export function initSmoothScroll() {
  create();
  bindAnchors();
  desktop.addEventListener?.("change", () => (desktop.matches ? create() : destroy()));
  onReducedChange(() => (reduced() ? destroy() : create()));
}
