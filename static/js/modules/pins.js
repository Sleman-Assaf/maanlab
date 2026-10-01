/*
 * Bottom-pinned curtains (ORYN hero/FAQ pattern): a sticky section whose
 * `top` is negative, so it scrolls until its bottom meets the viewport bottom,
 * then stays while the next section slides over it.
 *   top = min(viewportHeight − sectionHeight, data-pin-min)
 */
export function initPins() {
  const pins = [...document.querySelectorAll("[data-pin-bottom]")];
  if (!pins.length) return;

  const update = () => {
    pins.forEach((el) => {
      const query = el.dataset.pinMq || "(min-width: 1024px)";
      if (!window.matchMedia(query).matches) {
        el.style.removeProperty("--pin-top");
        return;
      }
      const floor = el.dataset.pinMin ? parseFloat(el.dataset.pinMin) : 0;
      const top = Math.min(window.innerHeight - el.offsetHeight, floor);
      el.style.setProperty("--pin-top", `${Math.round(top)}px`);
    });
  };

  let frame = 0;
  const schedule = () => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => {
      update();
      window.ScrollTrigger?.refresh();
    });
  };

  update();
  window.addEventListener("resize", schedule);
  if ("ResizeObserver" in window) {
    const ro = new ResizeObserver(schedule);
    pins.forEach((el) => ro.observe(el));
  }
}
