/*
 * Hero — ORYN entrance timeline + scroll behaviour.
 * The right column is an SVG workflow sketch that draws itself (hero-workflow.js)
 * inside this timeline, then a data dot loops through it. On scroll it responds
 * only subtly while the hero is covered by the Services curtain.
 */
import { EASE, hasGSAP, reduced } from "./env.js";
import { drawWorkflow, startAmbient, syncStroke } from "./hero-workflow.js";

export function initHero() {
  const hero = document.querySelector("[data-hero]");
  if (!hero) return;

  const q = (sel) => hero.querySelector(sel);
  const qa = (sel) => [...hero.querySelectorAll(sel)];
  const header = document.querySelector("[data-header]");
  const feature = q("[data-hero-feature]");
  const featureMedia = feature?.querySelector(".shutter");
  const workflow = q("[data-wf]");
  if (workflow) syncStroke(workflow);

  // Reduced motion / no GSAP: the complete sketch is shown as-is (no drawing, no data dot).
  if (reduced() || !hasGSAP()) {
    featureMedia?.classList.add("is-in");
    return;
  }

  const { gsap, ScrollTrigger } = window;
  const inEl = (name) => q(`[data-hero-in="${name}"]`);

  /* --- Entrance (on load) ----------------------------------------------- */
  const tl = gsap.timeline({ defaults: { ease: EASE.io } });
  tl.fromTo(q("[data-hero-bg]"), { opacity: 0, scale: 1.3, y: 40 }, { opacity: 1, scale: 1, y: 0, duration: 1, ease: EASE.bg }, 0)
    .fromTo(header, { opacity: 0, y: -80 }, { opacity: 1, y: 0, duration: 0.8, clearProps: "transform,opacity" }, 0.3)
    .fromTo(q("[data-hero-workflow]"), { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.6, ease: EASE.out }, 0.3)
    .fromTo(inEl("title"), { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 1.4 }, 0.4)
    .fromTo(inEl("eyebrow"), { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 1.4 }, 0.6)
    .fromTo(inEl("lead"), { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 1.4 }, 1.0)
    .fromTo(inEl("actions"), { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 1.4 }, 1.3)
    .fromTo(q("[data-hero-stats]"), { opacity: 0, y: -40 }, { opacity: 1, y: 0, duration: 0.8 }, 0.4)
    .fromTo(qa("[data-hero-stat]"), { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.7, stagger: 0.3 }, 1.0)
    .add(() => featureMedia?.classList.add("is-in"), 0.9)
    .fromTo(q("[data-hero-feature-body]"), { opacity: 0, y: 32 }, { opacity: 1, y: 0, duration: 0.6, ease: EASE.accent }, 1.1)
    .fromTo(inEl("cue"), { opacity: 0 }, { opacity: 1, duration: 0.8 }, 1.6);

  if (workflow) {
    const draw = drawWorkflow(workflow); // ≈3.4s → settles ≈3.8s after load
    tl.add(draw, 0.4).call(startAmbient, [workflow], 0.4 + draw.duration() + 0.3);
  }

  /* --- Scroll (desktop): subtle sketch response, parallax, curtain shade -- */
  const mm = gsap.matchMedia();
  mm.add("(min-width: 1200px)", () => {
    const range = { start: 0, end: () => `+=${hero.offsetHeight}`, scrub: 0.6, invalidateOnRefresh: true };
    gsap.to(q("[data-hero-scale]"), { scale: 1.08, y: -20, ease: "none", scrollTrigger: { ...range } });
    gsap.to(q("[data-hero-scale]"), {
      opacity: 0.8,
      ease: "none",
      scrollTrigger: { start: () => hero.offsetHeight * 0.6, end: () => hero.offsetHeight, scrub: true, invalidateOnRefresh: true },
    });
    gsap.to(q("[data-hero-bg-scale]"), { scale: 1.15, ease: "none", scrollTrigger: { ...range } });
    gsap.to(q("[data-hero-content]"), { y: -140, ease: "none", scrollTrigger: { ...range } });
    gsap.to(q("[data-hero-shade]"), {
      opacity: 0.55,
      ease: "none",
      scrollTrigger: { start: () => hero.offsetHeight * 0.3, end: () => hero.offsetHeight, scrub: true, invalidateOnRefresh: true },
    });
  });

  /* Tablet/mobile: no scroll transform on the sketch (kept simple). */

  ScrollTrigger.refresh();
}
