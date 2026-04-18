(function () {
  function initQuickTrack() {
    const form = document.querySelector("[data-quick-track-form]");
    if (!form) return;

    const input = form.querySelector("[data-quick-track-input]");
    const result = form.querySelector("[data-quick-track-result]");
    if (!input || !result) return;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();

      const trackingNumber = input.value.trim();
      if (!trackingNumber) {
        result.textContent = "Saisis un numéro de suivi.";
        result.classList.add("error");
        return;
      }

      result.textContent = "Recherche en cours...";
      result.classList.remove("error");

      try {
        const response = await fetch(`/api/track/${encodeURIComponent(trackingNumber)}`, {
          headers: { Accept: "application/json" },
        });

        const payload = await response.json();
        if (!response.ok) {
          const message = payload?.error?.message || "Colis introuvable.";
          result.textContent = message;
          result.classList.add("error");
          return;
        }

        const statusLabel = payload?.status?.label || payload?.status?.code || "Inconnu";
        const updatedAt = payload?.status?.updated_at || "N/A";
        result.textContent = `Statut: ${statusLabel} (mise à jour: ${updatedAt})`;
      } catch (_error) {
        result.textContent = "Erreur réseau, réessaie dans un instant.";
        result.classList.add("error");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initQuickTrack);
})();
