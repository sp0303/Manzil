// ---------- Navbar helpers ----------
// The navbar is injected via fetch() on each page, so these run once it appears.
const syncNav = () => {
  const nav = document.querySelector(".navbar");
  const logo = document.querySelector(".navbar-brand img");
  if (!nav || !logo) return;
  const scrolled = window.scrollY > 50;
  nav.classList.toggle("scrolled", scrolled);
  // Swap logo for contrast
  logo.src = scrolled ? "./pngs/SecondaryLogoBlack.png" : "./pngs/SecondaryLogoWhite.png";
};

// Highlight the menu item for the current page
const markActiveNav = () => {
  const current = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".navbar .nav-link").forEach((link) => {
    const isActive = link.getAttribute("href") === current;
    link.classList.toggle("active", isActive);
    if (isActive) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
};

const navbarHost = document.getElementById("navbar");
if (navbarHost) {
  const onNavbarReady = () => { markActiveNav(); syncNav(); };
  if (navbarHost.querySelector(".navbar")) onNavbarReady();
  new MutationObserver(onNavbarReady).observe(navbarHost, { childList: true });
}

window.addEventListener("scroll", syncNav, { passive: true });

// ---------- Preloader (home page only) ----------
// Hide shortly after the page has loaded, and never keep visitors waiting more than ~3s.
(() => {
  const preloader = document.getElementById("preloader");
  if (!preloader) return;

  document.body.classList.add("preloader-active");
  let done = false;
  const hide = () => {
    if (done) return;
    done = true;
    document.body.classList.add("loaded");               // triggers CSS fade-out
    document.body.classList.remove("preloader-active");  // re-enable scroll
    setTimeout(() => { preloader.style.display = "none"; }, 800);
    syncNav();
  };

  if (document.readyState === "complete") setTimeout(hide, 600);
  else window.addEventListener("load", () => setTimeout(hide, 600));
  setTimeout(hide, 3000);
})();

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
