/* Environment, feature flags and the shared easing vocabulary. */

export const html = document.documentElement;
export const isRTL = html.dir === "rtl";
export const dir = isRTL ? -1 : 1;
export const isArabic = (html.lang || "").toLowerCase().startsWith("ar");

const reducedQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
export const reducedMotion = reducedQuery;
export const reduced = () => reducedQuery.matches || html.classList.contains("rm");

export const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
export const saveData = () => Boolean(navigator.connection && navigator.connection.saveData);

/* Phones get the lighter video copy when one exists (same breakpoint as the layout). */
const phoneQuery = window.matchMedia("(max-width: 809px)");
export const videoSource = (desktop, phone) => (phone && phoneQuery.matches ? phone : desktop);

export const hasGSAP = () => Boolean(window.gsap && window.ScrollTrigger);

/* ORYN easing curves, registered with CustomEase when available. */
export const EASE = {
  io: "sine.inOut", // cubic-bezier(.44,0,.56,1)
  accent: "power2.in", // cubic-bezier(.5,0,.88,.77)
  out: "expo.out", // cubic-bezier(.22,1,.36,1)
  bg: "power3.inOut", // cubic-bezier(.68,0,.2,.89)
  land: "expo.out", // spring, no bounce
};

export function registerPlugins() {
  const { gsap } = window;
  if (!gsap) return;
  const plugins = [window.ScrollTrigger, window.Flip, window.SplitText, window.CustomEase].filter(Boolean);
  gsap.registerPlugin(...plugins);

  if (window.CustomEase) {
    const { CustomEase } = window;
    CustomEase.create("maan.io", ".44,0,.56,1");
    CustomEase.create("maan.accent", ".5,0,.88,.77");
    CustomEase.create("maan.out", ".22,1,.36,1");
    CustomEase.create("maan.bg", ".68,0,.2,.89");
    CustomEase.create("maan.land", ".16,1,.3,1");
    Object.assign(EASE, {
      io: "maan.io",
      accent: "maan.accent",
      out: "maan.out",
      bg: "maan.bg",
      land: "maan.land",
    });
  }

  if (window.ScrollTrigger) {
    window.ScrollTrigger.config({ ignoreMobileResize: true });
  }
}

export function onReducedChange(callback) {
  reducedQuery.addEventListener?.("change", callback);
}
