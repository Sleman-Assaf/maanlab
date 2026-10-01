/*
 * Hero workflow sketch — draws the SVG line by line (pathLength="1" +
 * stroke-dashoffset), then a small orange data dot travels the flow on a loop.
 *
 *   drawWorkflow(svg)   → GSAP timeline (≈3.4s) to nest in the hero timeline
 *   startAmbient(svg)   → looping data dot + subtle node pulses
 *
 * Mobile (≤809px) hides the database/API branch via CSS; the timeline and the
 * dot route only use what is visible.
 */
import { EASE } from "./env.js";

const compactQuery = window.matchMedia("(max-width: 809.98px)");

/* Rendered at the current breakpoint (neither it nor an ancestor is display:none). */
const visible = (el) => Boolean(el) && [el, ...parents(el)].every((node) => getComputedStyle(node).display !== "none");

function parents(el) {
  const list = [];
  let node = el.parentElement;
  while (node && node.tagName.toLowerCase() !== "svg") {
    list.push(node);
    node = node.parentElement;
  }
  return list;
}

/* Keep strokes ~1.4px on screen whatever size the SVG is rendered at. */
export function syncStroke(svg) {
  const update = () => {
    const height = svg.getBoundingClientRect().height || 1;
    svg.style.setProperty("--wf-sw", ((1.45 * 760) / height).toFixed(2));
  };
  update();
  if ("ResizeObserver" in window) new ResizeObserver(update).observe(svg);
}

export function drawWorkflow(svg) {
  const { gsap } = window;
  const step = (name) => svg.querySelector(`[data-wf-step="${name}"]`);
  const draws = (root, selector = ".wf-draw") =>
    root ? [...(root.matches?.(selector) ? [root] : []), ...root.querySelectorAll(selector)].filter(visible) : [];
  const part = (name, key) => step(name)?.querySelector(`[data-wf-part="${key}"]`);

  const tl = gsap.timeline({ defaults: { ease: "power2.inOut" } });
  const draw = (targets, at, duration, stagger = 0) => {
    if (targets.length) {
      tl.fromTo(targets, { strokeDashoffset: 1, opacity: 0 }, { strokeDashoffset: 0, opacity: 1, duration, stagger }, at);
    }
  };
  const node = (name, at) => {
    const el = step(name);
    if (el && visible(el)) {
      tl.fromTo(el, { opacity: 0, scale: 0.96, y: 6, transformOrigin: "50% 50%" }, { opacity: 1, scale: 1, y: 0, duration: 0.6, ease: EASE.out }, at);
    }
  };

  // Construction marks fade in first (they are never "drawn").
  tl.fromTo(svg.querySelector("[data-wf-guides]"), { opacity: 0 }, { opacity: 1, duration: 1.2, ease: "none" }, 0);

  // 01 Input — frame (0.4→1.2s page time), then chrome + grid quickly, then the accent cell.
  draw(draws(part("sheet", "frame")), 0, 0.5, 0.1);
  draw(draws(part("sheet", "chrome")), 0.45, 0.35, 0.08);
  draw(draws(part("sheet", "grid")), 0.6, 0.35, 0.07);
  draw(draws(part("sheet", "accent")), 0.9, 0.3);

  // Link → 02 Automation → link → 03 AI
  draw(draws(step("link-a")), 0.6, 0.5);
  node("automation", 0.9);
  draw(draws(step("automation")), 0.9, 0.45, 0.12);
  draw(draws(step("link-b")), 1.4, 0.4);
  node("ai", 1.5);
  draw(draws(step("ai")), 1.5, 0.45, 0.12);

  // 04 Connected systems (desktop/tablet) or direct link (mobile)
  if (visible(step("branches"))) {
    draw(draws(step("branches")), 2.0, 0.45);
    node("database", 2.2);
    draw(draws(step("database")), 2.2, 0.4, 0.1);
    node("api", 2.3);
    draw(draws(step("api")), 2.3, 0.4, 0.1);
    draw(draws(step("merges")), 2.6, 0.35);
  } else {
    draw(draws(step("direct")), 2.0, 0.6);
  }

  // 05 Output — report, then the message bubble (settles ≈3.8s page time)
  node("result", 2.7);
  draw(draws(step("result")), 2.7, 0.4, 0.1);

  // Anything hidden at load (other breakpoint) ends fully drawn, so resizing later still shows it.
  tl.add(() => gsap.set(svg.querySelectorAll(".wf-draw"), { strokeDashoffset: 0, opacity: 1 }));
  return tl;
}

export function startAmbient(svg) {
  const { gsap } = window;
  const dot = svg.querySelector("[data-wf-dot]");
  if (!dot) return;

  const anchors = [
    { step: "sheet", x: 271, y: 150 },
    { step: "automation", x: 303, y: 277 },
    { step: "ai", x: 285, y: 414 },
    { step: "database", x: 180, y: 572, full: true },
    { step: "result", x: 238, y: 700 },
  ];

  let loop = null;
  let inView = true;

  const build = () => {
    loop?.kill();
    const mode = compactQuery.matches ? "compact" : "full";
    const route = svg.querySelector(`[data-wf-route="${mode}"]`);
    const length = route.getTotalLength();

    // Where along the route each node sits → trigger a tiny pulse when the dot passes.
    const marks = anchors
      .filter((a) => mode === "full" || !a.full)
      .map((a) => {
        let best = 0;
        let bestDistance = Infinity;
        for (let l = 0; l <= length; l += 2) {
          const p = route.getPointAtLength(l);
          const d = (p.x - a.x) ** 2 + (p.y - a.y) ** 2;
          if (d < bestDistance) {
            bestDistance = d;
            best = l;
          }
        }
        return { at: best / length, el: svg.querySelector(`[data-wf-step="${a.step}"]`) };
      });

    const state = { p: 0 };
    let last = 0;
    const place = () => {
      const point = route.getPointAtLength(state.p * length);
      dot.setAttribute("transform", `translate(${point.x.toFixed(1)} ${point.y.toFixed(1)})`);
      marks.forEach((mark) => {
        if (last < mark.at && state.p >= mark.at && mark.el) {
          gsap.fromTo(mark.el, { scale: 1 }, { scale: 1.035, duration: 0.3, yoyo: true, repeat: 1, ease: "sine.inOut", transformOrigin: "50% 50%", overwrite: "auto" });
        }
      });
      last = state.p;
    };

    loop = gsap.timeline({ repeat: -1, repeatDelay: 1, paused: !inView });
    loop
      .set(state, { p: 0, onComplete: () => (last = 0) })
      .to(dot, { opacity: 1, duration: 0.4, ease: "none" }, 0)
      .to(state, { p: 1, duration: 6, ease: "sine.inOut", onUpdate: place }, 0)
      .to(dot, { opacity: 0, duration: 0.4, ease: "none" }, 5.6);
    place();
  };

  build();
  compactQuery.addEventListener?.("change", build);

  // Pause the loop while the hero is off screen.
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting;
      if (loop) (inView ? loop.play() : loop.pause());
    }).observe(svg);
  }
}
