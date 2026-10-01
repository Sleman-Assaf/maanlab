/* AI video reel — clip-path inset opens to full-bleed on scroll; media settles from 1.18 → 1. */
import { hasGSAP, reduced } from "./env.js";

export function initReel() {
  const reel = document.querySelector("[data-reel]");
  if (!reel || reduced() || !hasGSAP()) return;

  const { gsap } = window;
  const frame = reel.querySelector("[data-reel-frame]");
  const media = reel.querySelector("[data-reel-media]");
  const mm = gsap.matchMedia();

  mm.add("(min-width: 810px)", () => {
    gsap.fromTo(
      frame,
      { clipPath: "inset(9% 11% round 28px)" },
      {
        clipPath: "inset(0% 0% round 0px)",
        ease: "none",
        scrollTrigger: { trigger: frame, start: "top 85%", end: "center 55%", scrub: 0.6 },
      }
    );
    gsap.fromTo(
      media,
      { scale: 1.18 },
      { scale: 1, ease: "none", scrollTrigger: { trigger: frame, start: "top bottom", end: "bottom top", scrub: 0.6 } }
    );
  });

  mm.add("(max-width: 809px)", () => {
    gsap.fromTo(
      media,
      { scale: 1.12 },
      { scale: 1, ease: "none", scrollTrigger: { trigger: frame, start: "top bottom", end: "bottom top", scrub: 0.6 } }
    );
  });
}

/* Film-style timecode (24 fps) driven by any video inside a .film-ui container. */
export function initTimecodes(root = document) {
  root.querySelectorAll("[data-timecode]").forEach((tc) => {
    const host = tc.closest(".reel__frame, .stage-layer");
    const video = host?.querySelector("video");
    if (!video) return;
    const pad = (n) => String(Math.floor(n)).padStart(2, "0");
    let raf = 0;
    const render = () => {
      const t = video.currentTime || 0;
      tc.textContent = `${pad(t / 3600)}:${pad((t / 60) % 60)}:${pad(t % 60)}:${pad((t % 1) * 24)}`;
      raf = video.paused ? 0 : window.requestAnimationFrame(render);
    };
    video.addEventListener("play", () => {
      if (!raf) raf = window.requestAnimationFrame(render);
    });
    video.addEventListener("pause", render);
  });
}
