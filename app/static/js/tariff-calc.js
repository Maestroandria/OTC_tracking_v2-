(function () {
  function formatAr(value) {
    return `${new Intl.NumberFormat("fr-FR").format(Math.round(value))} Ar`;
  }

  function initTariffCalc() {
    const form = document.querySelector("[data-tariff-form]");
    if (!form) return;

    const serviceInput = form.querySelector("[data-tariff-service]");
    const weightInput = form.querySelector("[data-tariff-weight]");
    const result = form.querySelector("[data-tariff-result]");
    if (!serviceInput || !weightInput || !result) return;

    const RATE_BY_SERVICE = {
      normal: 70000,
      express: 83000,
      liquide_poudre: 95000,
      batterie: 136000,
    };

    const LABEL_BY_SERVICE = {
      normal: "Normal",
      express: "Express",
      liquide_poudre: "Liquide & Poudre",
      batterie: "Batterie",
    };

    form.addEventListener("submit", (event) => {
      event.preventDefault();

      const service = serviceInput.value;
      const weight = parseFloat(weightInput.value || "0");

      if (!(weight > 0)) {
        result.textContent = "Renseigne un poids supérieur à 0 pour calculer.";
        result.classList.add("error");
        return;
      }

      const rate = RATE_BY_SERVICE[service] || RATE_BY_SERVICE.normal;
      const label = LABEL_BY_SERVICE[service] || LABEL_BY_SERVICE.normal;
      const total = weight * rate;

      result.textContent = `Tarif provisoire: ${formatAr(total)} (${label} — ${formatAr(rate)}/kg × ${weight} kg).`;
      result.classList.remove("error");
    });
  }

  document.addEventListener("DOMContentLoaded", initTariffCalc);
})();
