(function () {
  const STORAGE_KEY = "osl-ui-theme";

  function applyTheme(theme) {
    const body = document.body;
    if (!body) return;
    body.classList.toggle("theme-dark", theme === "dark");
    body.classList.add("theme-twitter");

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const isDark = theme === "dark";
      button.setAttribute("aria-pressed", String(isDark));
      button.setAttribute("aria-label", isDark ? "Activer le theme clair" : "Activer le theme sombre");
      button.dataset.themeIcon = isDark ? "☀️" : "🌙";
      button.textContent = isDark ? "☀️ Clair" : "🌙 Sombre";
    });
  }

  function initThemeToggle() {
    const savedTheme = localStorage.getItem(STORAGE_KEY);
    const preferDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
    const initialTheme = savedTheme || (preferDark ? "dark" : "light");
    applyTheme(initialTheme);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const isDark = document.body.classList.contains("theme-dark");
        const nextTheme = isDark ? "light" : "dark";
        localStorage.setItem(STORAGE_KEY, nextTheme);
        applyTheme(nextTheme);
      });
    });
  }

  function initScrollSpy() {
    const navLinks = Array.from(document.querySelectorAll("a[href^='#']"));
    const sectionIds = navLinks
      .map((link) => link.getAttribute("href"))
      .filter((href) => href && href.length > 1)
      .map((href) => href.slice(1));

    if (!sectionIds.length) return;

    const sectionMap = new Map();
    sectionIds.forEach((id) => {
      const section = document.getElementById(id);
      if (section) sectionMap.set(id, section);
    });

    if (!sectionMap.size) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const id = entry.target.getAttribute("id");
          if (!id) return;
          const link = navLinks.find((item) => item.getAttribute("href") === `#${id}`);
          if (!link) return;

          if (entry.isIntersecting) {
            navLinks.forEach((item) => item.classList.remove("is-active"));
            link.classList.add("is-active");
          }
        });
      },
      { threshold: 0.4 }
    );

    sectionMap.forEach((section) => observer.observe(section));
  }

  function initReveal() {
    const items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;

    const observer = new IntersectionObserver(
      (entries, io) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        });
      },
      { threshold: 0.15 }
    );

    items.forEach((item) => observer.observe(item));
  }

  function toast(message, isError) {
    let root = document.getElementById("osl-toast");
    if (!root) {
      root = document.createElement("div");
      root.id = "osl-toast";
      root.className = "osl-toast";
      document.body.appendChild(root);
    }

    root.textContent = message;
    root.classList.toggle("error", Boolean(isError));
    root.classList.add("show");

    clearTimeout(root._timer);
    root._timer = setTimeout(() => root.classList.remove("show"), 2200);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initThemeToggle();
    initScrollSpy();
    initReveal();
  });

  window.OSLUI = {
    toast,
  };
})();
