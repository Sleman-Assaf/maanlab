/*
 * Services — the ORYN Visual-FAQ mechanics, promoted to a pinned storyteller.
 * ≥1024px: a sticky viewport; scroll progress selects the active service and
 *          crossfades the media stage. Clicking a service scrolls to it.
 * <1024px: single-open accordion with inline media.
 * No JS:   every service is open and its media is shown inline.
 */
import { hasGSAP } from "./env.js";
import { scrollToY } from "./smooth-scroll.js";

export function initServices() {
  const root = document.querySelector("[data-services]");
  if (!root) return;
  const section = root.closest(".services");
  const items = [...root.querySelectorAll("[data-svc]")];
  const buttons = items.map((item) => item.querySelector("[data-svc-btn]"));
  const panels = items.map((item) => item.querySelector("[data-svc-panel]"));
  const layers = [...root.querySelectorAll("[data-svc-layer]")];
  const stage = root.querySelector("[data-svc-stage]");
  const count = items.length;
  const desktop = window.matchMedia("(min-width: 1024px)");

  let active = 0;
  let mode = "accordion";
  let trigger = null;
  let stageVisible = false;

  section.style.setProperty("--svc-count", count);
  // Collapse the panels instantly on setup (no transition), so the page height
  // is final before any ScrollTrigger measures positions below this section.
  section.classList.add("is-enhanced", "no-transition");
  void section.offsetHeight;
  window.requestAnimationFrame(() => window.requestAnimationFrame(() => section.classList.remove("no-transition")));

  const stageVideo = (layer) => layer?.querySelector("[data-stage-video]");

  const syncVideos = () => {
    layers.forEach((layer, index) => {
      const video = stageVideo(layer);
      if (!video) return;
      const shouldPlay = mode === "story" && stageVisible && index === active;
      if (shouldPlay) {
        if (!video.src && video.dataset.src) video.src = video.dataset.src;
        video.play().catch(() => {});
      } else if (!video.paused) {
        video.pause();
      }
    });
  };

  function setActive(index) {
    active = index;
    items.forEach((item, i) => {
      const on = i === index;
      item.classList.toggle("is-active", on);
      buttons[i].setAttribute("aria-expanded", String(on));
      panels[i].setAttribute("aria-hidden", String(!on));
      panels[i].toggleAttribute("inert", !on);
    });
    layers.forEach((layer, i) => layer.classList.toggle("is-active", i === index));
    syncVideos();
  }

  function enterStory() {
    mode = "story";
    section.classList.add("is-story");
    if (hasGSAP()) {
      trigger = window.ScrollTrigger.create({
        trigger: root,
        start: "top top",
        end: "bottom bottom",
        invalidateOnRefresh: true,
        onUpdate(self) {
          section.style.setProperty("--svc-progress", self.progress.toFixed(4));
          const index = Math.min(count - 1, Math.floor(self.progress * count));
          if (index !== active) setActive(index);
        },
      });
      window.ScrollTrigger.refresh();
    }
    syncVideos();
  }

  function exitStory() {
    trigger?.kill();
    trigger = null;
    mode = "accordion";
    section.classList.remove("is-story");
    if (hasGSAP()) window.ScrollTrigger.refresh();
    syncVideos();
  }

  buttons.forEach((button, index) => {
    button.addEventListener("click", () => {
      if (mode === "story") {
        const top = root.getBoundingClientRect().top + window.scrollY;
        const span = root.offsetHeight - window.innerHeight;
        scrollToY(top + span * ((index + 0.5) / count));
      } else {
        setActive(index);
      }
    });

    button.addEventListener("keydown", (event) => {
      const keys = { ArrowDown: index + 1, ArrowUp: index - 1, Home: 0, End: count - 1 };
      if (!(event.key in keys)) return;
      event.preventDefault();
      buttons[(keys[event.key] + count) % count].focus();
    });
  });

  if (stage && "IntersectionObserver" in window) {
    new IntersectionObserver(
      ([entry]) => {
        stageVisible = entry.isIntersecting;
        syncVideos();
      },
      { threshold: 0.25 }
    ).observe(stage);
  }

  setActive(0);
  const apply = () => (desktop.matches ? enterStory() : exitStory());
  apply();
  desktop.addEventListener?.("change", apply);
}
