/*
 * Headline blur-in (ORYN "appear" text effect).
 *
 * Latin: each character from blur(10px) + opacity 0 + y 10 → rest, 0.05s stagger.
 *
 * Arabic: splitting Arabic into characters breaks letter joining, so instead each
 * line is revealed by a soft mask that sweeps in reading direction (right → left)
 * while the line un-blurs and settles. Visually it reads as the same letter-by-
 * letter wave, with the text left intact and correctly shaped.
 */
import { EASE, hasGSAP, isArabic, reduced } from "./env.js";

/*
 * Run `play` once when `el` reaches 88% of the viewport. `clamp()` keeps
 * triggers near the page end reachable; elements already on screen at load
 * (e.g. a project title) play immediately instead of waiting for a scroll.
 */
function whenVisible(el, play) {
  const { ScrollTrigger } = window;
  if (el.getBoundingClientRect().top < window.innerHeight * 0.88) {
    play();
    return;
  }
  ScrollTrigger.create({ trigger: el, start: "clamp(top 88%)", once: true, onEnter: play });
}

function latin(el, gsap, SplitText) {
  const split = SplitText.create(el, {
    type: "words,chars",
    wordsClass: "split-word",
    charsClass: "split-char",
    aria: "auto",
  });
  const chars = split.chars;
  gsap.set(chars, { opacity: 0, y: 10, filter: "blur(10px)" });
  el.classList.add("is-split");

  const stagger = Math.min(0.05, 1.3 / Math.max(chars.length, 1));
  whenVisible(el, () =>
    gsap.to(chars, {
      opacity: 1,
      y: 0,
      filter: "blur(0px)",
      duration: 0.5,
      ease: EASE.out,
      stagger,
      delay: parseFloat(el.dataset.splitDelay || "0.25"),
      onComplete: () => gsap.set(chars, { clearProps: "filter,willChange" }),
    })
  );
}

function arabic(el, gsap) {
  const lines = el.querySelectorAll(".line").length ? [...el.querySelectorAll(".line")] : [el];
  lines.forEach((line) => line.classList.add("rv-line"));
  gsap.set(lines, { "--rv": 0, y: 10, filter: "blur(10px)" });
  el.classList.add("is-split");

  whenVisible(el, () => {
    const delay = parseFloat(el.dataset.splitDelay || "0.25");
    lines.forEach((line, index) => {
      // Sweep duration follows the line length, like the per-character stagger.
      const length = Math.max(line.textContent.trim().length, 4);
      const sweep = Math.min(1.6, 0.45 + length * 0.05);
      const at = delay + index * 0.3;
      gsap.to(line, { "--rv": 130, duration: sweep, ease: "power1.inOut", delay: at });
      gsap.to(line, {
        y: 0,
        filter: "blur(0px)",
        duration: sweep * 0.9,
        ease: EASE.out,
        delay: at,
        onComplete: () => {
          line.classList.remove("rv-line");
          gsap.set(line, { clearProps: "filter,transform,--rv" });
        },
      });
    });
  });
}

export function initSplitHeadings(root = document) {
  const headings = [...root.querySelectorAll("[data-split]")];
  if (!headings.length) return;

  if (reduced() || !hasGSAP() || (!isArabic && !window.SplitText)) {
    headings.forEach((el) => el.classList.add("is-split"));
    return;
  }

  const { gsap, SplitText } = window;
  headings.forEach((el) => (isArabic ? arabic(el, gsap) : latin(el, gsap, SplitText)));
}
