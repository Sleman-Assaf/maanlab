/*
 * MAAN LAB — progressive enhancement entry point.
 * Every page is fully server-rendered by Django; this file only adds motion
 * and interaction. Each module is isolated: one failure never blocks the rest,
 * and any failure reveals all content (html.anim-fallback).
 */
import { html, registerPlugins } from "./modules/env.js";
import { initSmoothScroll } from "./modules/smooth-scroll.js";
import { initHeader } from "./modules/header.js";
import { initPins } from "./modules/pins.js";
import { initHero } from "./modules/hero.js";
import { initReveals } from "./modules/reveal.js";
import { initSplitHeadings } from "./modules/split.js";
import { initServices } from "./modules/services.js";
import { initReel, initTimecodes } from "./modules/reel.js";
import { initProjects, initCardMedia } from "./modules/projects.js";
import { initCounters } from "./modules/counters.js";
import { initVideos } from "./modules/videos.js";
import { initContact } from "./modules/contact.js";
import { initLanguageSwitch } from "./modules/lang.js";
import { initProjectPage } from "./modules/project-page.js";

function safely(name, fn) {
  try {
    fn();
  } catch (error) {
    html.classList.add("anim-fallback");
    console.error(`[maan] ${name} failed`, error);
  }
}

function boot() {
  safely("plugins", registerPlugins);
  safely("smooth-scroll", initSmoothScroll);
  safely("pins", initPins);
  safely("header", initHeader);
  safely("hero", initHero);
  safely("services", initServices);
  safely("split", () => initSplitHeadings());
  safely("reveals", () => initReveals());
  safely("reel", initReel);
  safely("timecodes", () => initTimecodes());
  safely("projects", initProjects);
  safely("card-media", () => !document.querySelector("[data-projects]") && initCardMedia());
  safely("counters", () => initCounters());
  safely("videos", () => initVideos());
  safely("contact", initContact);
  safely("lang", initLanguageSwitch);
  safely("project-page", initProjectPage);

  safely("layout-watch", watchLayout);

  window.__maanReady = true;
  html.classList.add("is-ready");
}

/*
 * Keep ScrollTrigger positions correct when the page height changes after
 * boot — web fonts swapping in (Arabic especially), lazy media, accordion
 * toggles, filtering. Stale positions would leave animations unfired.
 */
function watchLayout() {
  const { ScrollTrigger } = window;
  if (!ScrollTrigger) return;
  let timer = 0;
  let lastHeight = document.documentElement.scrollHeight;
  const refresh = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const height = document.documentElement.scrollHeight;
      if (Math.abs(height - lastHeight) > 2) {
        lastHeight = height;
        ScrollTrigger.refresh();
      }
    }, 150);
  };
  if ("ResizeObserver" in window) new ResizeObserver(refresh).observe(document.body);
  document.fonts?.addEventListener?.("loadingdone", () => ScrollTrigger.refresh());
  window.addEventListener("load", () => ScrollTrigger.refresh());
}

const fontsReady = document.fonts?.ready ?? Promise.resolve();
Promise.race([fontsReady, new Promise((resolve) => setTimeout(resolve, 1200))]).then(boot);
