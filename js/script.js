
// ---------- Preloader (5 seconds) ----------
window.addEventListener("DOMContentLoaded", () => {
  const preloader = document.getElementById("preloader");
  const nav = document.querySelector(".navbar");
  const logo = document.querySelector(".navbar-brand img");

  // Helper to sync navbar state with current scroll position
  const syncNav = () => {
    if (!nav || !logo) return;
    const scrolled = window.scrollY > 50;
    nav.classList.toggle("scrolled", scrolled);
    logo.src = scrolled ? "./pngs/SecondaryLogoBlack.png" : "./pngs/SecondaryLogoWhite.png";
  };

  if (preloader) {
    // Keep the preloader visible for a full 5 seconds
    setTimeout(() => {
      document.body.classList.add("loaded");
      preloader.style.display = "none";
      // After showing the page, sync navbar once (in case user has already scrolled)
      syncNav();
    }, 5000);
  } else {
    // No preloader present — just sync immediately
    syncNav();
  }

  // Also sync once right away in case there's no preloader delay
  // (harmless if preloader exists; we'll sync again after it hides)
  syncNav();
});

// ---------- Navbar scroll behavior ----------
window.addEventListener("scroll", () => {
  const nav = document.querySelector(".navbar");
  const logo = document.querySelector(".navbar-brand img");
  if (!nav || !logo) return;

  const scrolled = window.scrollY > 50;
  nav.classList.toggle("scrolled", scrolled);

  // Swap logo for contrast
  logo.src = scrolled ? "./pngs/SecondaryLogoBlack.png" : "./pngs/SecondaryLogoWhite.png";
}, { passive: true });

// ---------- Video resilience (pause on reduced motion) ----------
(() => {
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  const video = document.querySelector(".bg-video");
  if (!video) return;

  const applyMotionPreference = () => {
    if (mq.matches) {
      video.pause();
      video.removeAttribute("autoplay");
    } else {
      video.play().catch(() => {});
    }
  };

  // addEventListener for modern browsers, addListener fallback for older ones
  if (mq.addEventListener) {
    mq.addEventListener("change", applyMotionPreference);
  } else if (mq.addListener) {
    mq.addListener(applyMotionPreference);
  }
  applyMotionPreference();
})();
