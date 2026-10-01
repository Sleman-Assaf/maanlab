/*
 * Video manager: lazy-load sources near the viewport, autoplay (muted) only
 * while visible, pause offscreen and when the tab is hidden, and wire the
 * accessible play/pause toggles. Reduced motion / Save-Data → no autoplay.
 */
import { reduced, saveData, videoSource } from "./env.js";

export function initVideos(root = document) {
  const videos = [...root.querySelectorAll("video[data-inview-play]")];
  const autoplay = !reduced() && !saveData();
  const userPaused = new WeakSet();

  const load = (video) => {
    if (video.dataset.src && !video.getAttribute("src")) {
      video.src = videoSource(video.dataset.src, video.dataset.srcMobile);
      video.preload = "metadata";
    }
  };

  const toggleFor = (video) => video.closest(".reel__frame, .project-cover__frame")?.querySelector("[data-video-toggle]");

  const syncToggle = (video) => {
    const toggle = toggleFor(video);
    if (!toggle) return;
    const paused = video.paused;
    toggle.setAttribute("aria-pressed", String(paused));
    const label = toggle.querySelector("[data-video-toggle-label]");
    if (label) label.textContent = paused ? toggle.dataset.labelPlay : toggle.dataset.labelPause;
  };

  if (!autoplay) {
    videos.forEach((video) => {
      video.removeAttribute("autoplay");
      video.pause();
      load(video);
    });
  }

  if ("IntersectionObserver" in window) {
    const near = new IntersectionObserver(
      (entries, observer) =>
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            load(entry.target);
            observer.unobserve(entry.target);
          }
        }),
      { rootMargin: "300px 0px" }
    );
    const visible = new IntersectionObserver(
      (entries) =>
        entries.forEach((entry) => {
          const video = entry.target;
          if (entry.isIntersecting && autoplay && !userPaused.has(video)) {
            load(video);
            video.play().catch(() => {});
          } else if (!entry.isIntersecting && !video.paused) {
            video.pause();
          }
        }),
      { threshold: 0.25 }
    );
    videos.forEach((video) => {
      near.observe(video);
      visible.observe(video);
    });
  } else {
    videos.forEach(load);
  }

  videos.forEach((video) => {
    video.addEventListener("play", () => syncToggle(video));
    video.addEventListener("pause", () => syncToggle(video));
    syncToggle(video);
    const toggle = toggleFor(video);
    toggle?.addEventListener("click", () => {
      load(video);
      if (video.paused) {
        userPaused.delete(video);
        video.play().catch(() => {});
      } else {
        userPaused.add(video);
        video.pause();
      }
    });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) document.querySelectorAll("video").forEach((v) => !v.paused && v.pause());
  });
}
