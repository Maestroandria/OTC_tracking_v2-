(function () {
  function initClickMenu() {
    const menu = document.querySelector("[data-menu-toggle]");
    if (!menu) return;

    const trigger = menu.querySelector("[data-menu-trigger]");
    if (!trigger) return;

    const openMenu = () => {
      menu.classList.add("is-open");
      trigger.setAttribute("aria-expanded", "true");
    };

    const closeMenu = () => {
      menu.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
    };

    trigger.addEventListener("click", () => {
      const isOpen = menu.classList.contains("is-open");
      if (isOpen) {
        closeMenu();
        return;
      }
      openMenu();
    });

    document.addEventListener("click", (event) => {
      if (!menu.contains(event.target)) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeMenu();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initClickMenu);
})();
