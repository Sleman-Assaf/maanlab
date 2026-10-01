/* Project detail page — cover media settles from 1.12 → 1 while scrolling past (parallax). */
import { hasGSAP, reduced } from "./env.js";

export function initProjectPage() {
  const cover = document.querySelector("[data-project-cover]");
  if (!cover || reduced() || !hasGSAP()) return;
  const media = cover.querySelector("[data-project-cover-media]");
  window.gsap.fromTo(
    media,
    { scale: 1.12, yPercent: -3 },
    {
      scale: 1,
      yPercent: 3,
      ease: "none",
      scrollTrigger: { trigger: cover, start: "top bottom", end: "bottom top", scrub: 0.6 },
    }
  );
}
