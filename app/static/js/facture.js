function initFacturePage() {
  const factureForm = document.getElementById("facture-form");
  const itemsTable = document.getElementById("items-table");
  const addLineButton = document.getElementById("add-line-button");
  const deviseInput = document.getElementById("devise");
  const totalOutput = document.getElementById("total");
  const deviseTotalOutput = document.getElementById("devise-total");
  const rowTemplate = document.getElementById("facture-row-template");
  const clientsDataElement = document.getElementById("clients-data");
  const clientCodeInput = document.getElementById("client_code");
  const clientNameInput = document.getElementById("client_raison_sociale");
  const clientAddressInput = document.getElementById("client_adresse");
  const clientNifInput = document.getElementById("client_nif");
  const clientStatInput = document.getElementById("client_stat");
  const clientRibInput = document.getElementById("client_rib");
  const clientPanel = document.getElementById("facture-client-panel");

  if (!itemsTable || !addLineButton || !deviseInput || !totalOutput || !deviseTotalOutput || !rowTemplate) {
    return;
  }

  const tableBody = itemsTable.tBodies[0];
  if (!tableBody) {
    return;
  }

  let clientsIndex = {};
  try {
    const rawClients = JSON.parse(clientsDataElement?.dataset?.clients || "[]");
    clientsIndex = rawClients.reduce((acc, client) => {
      const code = String(client.code_client || "").trim();
      if (code) {
        acc[code] = client;
      }
      return acc;
    }, {});
  } catch (_err) {
    clientsIndex = {};
  }

  const clientFields = [
    clientNameInput,
    clientAddressInput,
    clientNifInput,
    clientStatInput,
    clientRibInput,
  ].filter(Boolean);

  function setClientFieldsRequired(isRequired) {
    clientFields.forEach((field) => {
      field.required = isRequired;
    });
  }

  function clearClientFields() {
    clientFields.forEach((field) => {
      field.value = "";
    });
  }

  function isKnownClientCode() {
    const code = clientCodeInput?.value.trim() || "";
    return Boolean(code && clientsIndex[code]);
  }

  function autofillClientFields() {
    if (!clientCodeInput) {
      return;
    }

    const code = clientCodeInput.value.trim();
    const client = clientsIndex[code];
    if (!client) {
      setClientFieldsRequired(true);
      if (code) {
        clearClientFields();
        if (clientPanel) {
          clientPanel.open = true;
        }
      }
      return;
    }

    setClientFieldsRequired(true);

    if (clientNameInput) clientNameInput.value = client.raison_sociale || "";
    if (clientAddressInput) clientAddressInput.value = client.adresse || "";
    if (clientNifInput) clientNifInput.value = client.nif || "";
    if (clientStatInput) clientStatInput.value = client.stat || "";
    if (clientRibInput) clientRibInput.value = client.rib || "";
  }

  function updateMontantLigne(row) {
    const unitPriceInput = row.querySelector('input[name="unit_price"]');
    const quantityInput = row.querySelector('input[name="quantity"]');
    const montantInput = row.querySelector("input.montant-ligne");

    const unitPrice = parseFloat(unitPriceInput?.value || "0") || 0;
    const quantity = parseFloat(quantityInput?.value || "0") || 0;
    const montant = unitPrice * quantity;

    if (montantInput) {
      montantInput.value = montant.toFixed(2);
    }
  }

  function updateTotal() {
    let total = 0;

    tableBody.querySelectorAll("tr").forEach((row) => {
      updateMontantLigne(row);
      const montantValue = parseFloat(row.querySelector("input.montant-ligne")?.value || "0") || 0;
      total += montantValue;
    });

    totalOutput.innerText = total.toFixed(2);
    deviseTotalOutput.innerText = deviseInput.value || "Ar";
  }

  function bindRowEvents(row) {
    const unitPriceInput = row.querySelector('input[name="unit_price"]');
    const quantityInput = row.querySelector('input[name="quantity"]');

    unitPriceInput?.addEventListener("input", updateTotal);
    quantityInput?.addEventListener("input", updateTotal);
  }

  function addRow() {
    const rowFragment = rowTemplate.content.cloneNode(true);
    const appendedRow = rowFragment.querySelector("tr");

    tableBody.appendChild(rowFragment);
    if (appendedRow) {
      bindRowEvents(appendedRow);
    }
    updateTotal();
  }

  function removeRow(row) {
    row.remove();

    if (!tableBody.querySelector("tr")) {
      addRow();
      return;
    }

    updateTotal();
  }

  addLineButton.addEventListener("click", addRow);

  tableBody.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const deleteButton = target.closest(".facture-btn-danger");
    if (!deleteButton) {
      return;
    }

    const row = deleteButton.closest("tr");
    if (row) {
      removeRow(row);
    }
  });

  tableBody.querySelectorAll("tr").forEach(bindRowEvents);
  deviseInput.addEventListener("input", updateTotal);
  clientCodeInput?.addEventListener("change", autofillClientFields);
  clientCodeInput?.addEventListener("blur", autofillClientFields);

  factureForm?.addEventListener("submit", () => {
    autofillClientFields();
    if (!isKnownClientCode() && clientPanel) {
      clientPanel.open = true;
      const firstMissingField = clientFields.find((field) => !String(field.value || "").trim());
      firstMissingField?.focus();
    }
  });

  updateTotal();
}

window.addEventListener("DOMContentLoaded", initFacturePage);
