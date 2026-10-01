/* Scroll reveals (ORYN fade-ups) + shutter image reveals, via one IntersectionObserver per threshold. */
import { reduced } from "./env.js";

export function initReveals(root = document) {
  const elements = [...root.querySelectorAll("[data-reveal], [data-shutter]")].filter(
    (el) => !el.closest("[data-hero]")
  );
  if (!elements.length) return;

  if (reduced() || !("IntersectionObserver" in window)) {
    elements.forEach((el) => el.classList.add("is-in"));
    return;
  }

  elements.forEach((el) => {
    const { revealDelay, revealY, revealDuration } = el.dataset;
    if (revealDelay) el.style.setProperty("--rdelay", `${parseFloat(revealDelay)}s`);
    if (revealY) el.style.setProperty("--ry", `${parseFloat(revealY)}px`);
    if (revealDuration) el.style.setProperty("--rd", `${parseFloat(revealDuration)}s`);
  });

  const observers = new Map();
  const observerFor = (threshold) => {
    if (!observers.has(threshold)) {
      observers.set(
        threshold,
        new IntersectionObserver(
          (entries, observer) => {
            entries.forEach((entry) => {
              if (entry.isIntersecting) {
                entry.target.classList.add("is-in");
                observer.unobserve(entry.target);
              }
            });
          },
          { threshold, rootMargin: "0px 0px -6% 0px" }
        )
      );
    }
    return observers.get(threshold);
  };

  elements.forEach((el) => {
    let threshold = parseFloat(el.dataset.revealThreshold || "0.12");
    // Elements taller than the viewport can never reach a high ratio.
    if (el.offsetHeight > window.innerHeight * 0.8) threshold = 0;
    observerFor(threshold).observe(el);
  });
}
