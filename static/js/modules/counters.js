/*
 * Digit-roller counters (ORYN tech-spec numbers): each digit is a clipped
 * column that rolls up from 0 to its value — 1.76s, easeInOut, 0.1s stagger.
 * The server-rendered number stays as the accessible label.
 */
import { hasGSAP, reduced } from "./env.js";

export function initCounters(root = document) {
  const counters = [...root.querySelectorAll("[data-counter]")];
  if (!counters.length || reduced() || !hasGSAP()) return;
  const { gsap, ScrollTrigger } = window;

  counters.forEach((el) => {
    const text = el.textContent.trim();
    if (!/\d/.test(text)) return;
    el.setAttribute("aria-label", text);
    el.classList.add("odo");

    const strips = [];
    el.innerHTML = "";
    [...text].forEach((char) => {
      if (!/\d/.test(char)) {
        const span = document.createElement("span");
        span.textContent = char;
        span.setAttribute("aria-hidden", "true");
        el.appendChild(span);
        return;
      }
      const col = document.createElement("span");
      col.className = "odo__col";
      col.setAttribute("aria-hidden", "true");
      const strip = document.createElement("span");
      strip.className = "odo__strip";
      for (let n = 0; n <= 9; n += 1) {
        const digit = document.createElement("span");
        digit.textContent = String(n);
        strip.appendChild(digit);
      }
      col.appendChild(strip);
      el.appendChild(col);
      strips.push({ strip, value: Number(char) });
    });

    const roll = () =>
      strips.forEach(({ strip, value }, index) =>
        gsap.to(strip, { yPercent: -value * 10, duration: 1.76, ease: "power1.inOut", delay: index * 0.1 })
      );
    // Already on screen at load → roll now; otherwise when 80% into view (clamped near the page end).
    if (el.getBoundingClientRect().top < window.innerHeight * 0.8) roll();
    else ScrollTrigger.create({ trigger: el, start: "clamp(top 80%)", once: true, onEnter: roll });
  });
}
