/*
 * Projects — client-side filtering of server-rendered cards (no reload) with
 * GSAP Flip layout transitions, plus card media interactions.
 * Without JS the filter pills are plain links (?category=…) handled by Django.
 */
import { EASE, finePointer, hasGSAP, reduced, saveData, videoSource } from "./env.js";
import { scrollToTarget } from "./smooth-scroll.js";

let playingCard = null;

function stopCard(card) {
  const video = card?.querySelector(".pcard__video:not(.pcard__video--base), .hero-feature__video");
  if (video && !video.paused) video.pause();
  card?.classList.remove("is-playing");
  if (playingCard === card) playingCard = null;
}

function playCard(card) {
  const source = videoSource(card.dataset.hoverVideo, card.dataset.hoverVideoMobile);
  const video = card.querySelector(".pcard__video:not(.pcard__video--base), .hero-feature__video");
  if (!source || !video) return;
  if (playingCard && playingCard !== card) stopCard(playingCard);
  if (!video.src) {
    video.src = source;
    video.preload = "auto";
  }
  playingCard = card;
  video
    .play()
    .then(() => {
      if (playingCard === card) card.classList.add("is-playing");
    })
    .catch(() => {});
}

/*
 * Hero AI-film card: its silent loop starts by itself, but only after the page has
 * finished loading (so it never competes with the first paint), only while the card
 * is on screen, and never on Save-Data, slow connections or reduced motion.
 */
function initHeroFilm(card) {
  const video = card.querySelector(".hero-feature__video");
  const slow = /(^|-)2g$/.test(navigator.connection?.effectiveType || "");
  if (!video || reduced() || saveData() || slow || !("IntersectionObserver" in window)) return;

  const start = () => {
    new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          // Fetch the loop only once the card is on screen (on phones it starts below the fold).
          if (!video.getAttribute("src")) {
            video.src = videoSource(card.dataset.hoverVideo, card.dataset.hoverVideoMobile);
            video.preload = "auto";
          }
          video.play().then(() => card.classList.add("is-playing")).catch(() => {});
        } else {
          video.pause();
        }
      },
      { threshold: 0.25 }
    ).observe(card);
  };
  const idle = () => (window.requestIdleCallback ? requestIdleCallback(start, { timeout: 2000 }) : setTimeout(start, 600));
  if (document.readyState === "complete") idle();
  else window.addEventListener("load", idle, { once: true });
}

export function initCardMedia(root = document) {
  const all = [...root.querySelectorAll("[data-hover-video]")];
  const heroFilm = all.find((card) => card.matches(".hero-feature__media"));
  const cards = all.filter((card) => card !== heroFilm);
  const autoplayAllowed = !reduced() && !saveData();
  if (heroFilm) initHeroFilm(heroFilm);

  if (finePointer.matches) {
    cards.forEach((card) => {
      const host = card.closest(".pcard") || card;
      host.addEventListener("pointerenter", () => autoplayAllowed && playCard(card));
      host.addEventListener("pointerleave", () => stopCard(card));
      host.addEventListener("focusin", () => autoplayAllowed && playCard(card));
      host.addEventListener("focusout", () => stopCard(card));
    });
  } else if (autoplayAllowed && "IntersectionObserver" in window) {
    // Touch: play the single card that is most in view.
    const ratios = new Map();
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => ratios.set(entry.target, entry.isIntersecting ? entry.intersectionRatio : 0));
        let best = null;
        let bestRatio = 0.6;
        ratios.forEach((ratio, card) => {
          if (ratio >= bestRatio && !card.closest("[hidden]")) {
            best = card;
            bestRatio = ratio;
          }
        });
        if (best) playCard(best);
        else if (playingCard) stopCard(playingCard);
      },
      { threshold: [0, 0.6, 0.8, 1] }
    );
    cards.forEach((card) => io.observe(card));
  }

  // Cursor badge ("View" / "Play") following the pointer inside card media.
  if (finePointer.matches && !reduced() && hasGSAP()) {
    root.querySelectorAll(".pcard").forEach((card) => {
      const media = card.querySelector(".pcard__media");
      const badge = card.querySelector("[data-cursor]");
      if (!media || !badge) return;
      const xTo = window.gsap.quickTo(badge, "x", { duration: 0.5, ease: "power3.out" });
      const yTo = window.gsap.quickTo(badge, "y", { duration: 0.5, ease: "power3.out" });
      media.addEventListener("pointermove", (event) => {
        const rect = media.getBoundingClientRect();
        xTo(event.clientX - rect.left);
        yTo(event.clientY - rect.top);
      });
      media.addEventListener("pointerenter", (event) => {
        const rect = media.getBoundingClientRect();
        window.gsap.set(badge, { x: event.clientX - rect.left, y: event.clientY - rect.top });
        card.classList.add("is-hover");
      });
      media.addEventListener("pointerleave", () => card.classList.remove("is-hover"));
    });
  }
}

export function initProjects() {
  const root = document.querySelector("[data-projects]");
  if (!root) return;

  const grid = root.querySelector("[data-project-grid]");
  const items = grid ? [...grid.children] : [];
  const filters = [...root.querySelectorAll("[data-filter]")];
  const status = root.querySelector("[data-filter-status]");
  const empty = root.querySelector("[data-empty]");
  const template = root.dataset.statusTemplate || "{count}/{total}";
  let current = filters.find((f) => f.getAttribute("aria-pressed") === "true")?.dataset.filter || "all";

  const announce = (visible) => {
    if (status) status.textContent = template.replace("{count}", visible).replace("{total}", items.length);
  };

  function apply(category, { animate = true } = {}) {
    if (category === current) return;
    current = category;
    filters.forEach((f) => f.setAttribute("aria-pressed", String(f.dataset.filter === category)));

    // data-category lists the main category plus any "also show under" ones.
    const matches = (el) => category === "all" || el.dataset.category.split(" ").includes(category);
    const useFlip = animate && hasGSAP() && window.Flip && !reduced();
    const state = useFlip ? window.Flip.getState(items) : null;
    const startHeight = grid ? grid.offsetHeight : 0;

    items.forEach((el) => {
      const show = matches(el);
      if (!show) stopCard(el.querySelector("[data-hover-video]"));
      el.hidden = !show;
      if (show) el.querySelectorAll("[data-shutter], [data-reveal]").forEach((n) => n.classList.add("is-in"));
    });

    const visible = items.filter((el) => !el.hidden).length;
    if (empty) empty.hidden = visible > 0;
    announce(visible);

    if (useFlip && grid) {
      // Absolute-positioned leaving items would collapse the grid mid-animation;
      // hold the old height and ease it to the new one instead.
      const endHeight = grid.offsetHeight;
      window.gsap.fromTo(
        grid,
        { height: startHeight },
        { height: endHeight, duration: 0.7, ease: EASE.io, clearProps: "height" }
      );
      window.Flip.from(state, {
        duration: 0.7,
        ease: EASE.io,
        scale: true,
        absolute: true,
        onEnter: (els) =>
          window.gsap.fromTo(els, { opacity: 0, scale: 0.96 }, { opacity: 1, scale: 1, duration: 0.6, delay: 0.15, ease: EASE.io }),
        onLeave: (els) => window.gsap.to(els, { opacity: 0, scale: 0.96, duration: 0.35, ease: EASE.io }),
        onComplete: () => window.ScrollTrigger?.refresh(),
      });
    } else {
      window.ScrollTrigger?.refresh();
    }

    const url = new URL(window.location.href);
    if (category === "all") url.searchParams.delete("category");
    else url.searchParams.set("category", category);
    url.hash = "projects";
    history.replaceState(null, "", url);
  }

  filters.forEach((filter) => {
    filter.setAttribute("role", "button");
    filter.addEventListener("click", (event) => {
      event.preventDefault();
      apply(filter.dataset.filter);
    });
    filter.addEventListener("keydown", (event) => {
      if (event.key === " ") {
        event.preventDefault();
        apply(filter.dataset.filter);
      }
    });
  });

  document.querySelectorAll("[data-filter-link]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      apply(link.dataset.filterLink);
      scrollToTarget(root);
    });
  });

  initCardMedia(document);
}
