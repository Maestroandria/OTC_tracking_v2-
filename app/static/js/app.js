function toJsonOrThrow(response) {
  return response.json().then((data) => {
    if (!response.ok) {
      const msg = data?.error?.message || data?.message || "Erreur API";
      throw new Error(msg);
    }
    return data;
  });
}

function renderTimeline(events) {
  const timeline = document.getElementById("timeline");
  if (!timeline) return;

  if (!events?.length) {
    timeline.innerHTML = '<div class="muted">Aucun événement disponible.</div>';
    return;
  }

  timeline.innerHTML = events
    .map(
      (event) => `
      <div class="timeline-item">
        <span class="badge badge-${String(event.code || "").toLowerCase()}">${event.code || "N/A"}</span>
        <div>
          <div><strong>${event.label || "-"}</strong> — ${event.location || "N/A"}</div>
          <div class="muted">${event.event_time || ""}</div>
          <div>${event.details || ""}</div>
        </div>
      </div>
    `
    )
    .join("");
}

function initTrackPage() {
  const trackPage = document.querySelector("[data-track-page]");
  if (!trackPage) return;

  const trackingNumber = trackPage.dataset.trackingNumber;
  const refreshButton = document.getElementById("refresh-track");
  const copyButton = document.getElementById("copy-link");
  const shareInput = document.getElementById("share-link");

  refreshButton?.addEventListener("click", async () => {
    const originalText = refreshButton.textContent;
    refreshButton.disabled = true;
    refreshButton.textContent = "Actualisation...";
    try {
      const data = await fetch(`/api/track/${encodeURIComponent(trackingNumber)}`).then(toJsonOrThrow);
      renderTimeline(data.events);
      window.OSLUI?.toast?.("Timeline mise à jour.");
    } catch (err) {
      window.OSLUI?.toast?.(err.message, true);
    } finally {
      refreshButton.disabled = false;
      refreshButton.textContent = originalText;
    }
  });

  copyButton?.addEventListener("click", async () => {
    if (!shareInput?.value) return;
    try {
      await navigator.clipboard.writeText(shareInput.value);
      copyButton.textContent = "Copié";
      window.OSLUI?.toast?.("Lien copié.");
      setTimeout(() => {
        copyButton.textContent = "Copier";
      }, 1200);
    } catch (_err) {
      window.OSLUI?.toast?.("Impossible de copier le lien", true);
    }
  });
}

function formToObject(formElement) {
  const formData = new FormData(formElement);
  return Object.fromEntries(formData.entries());
}

function initAdminPage() {
  const createShipmentForm = document.getElementById("create-shipment-form");
  const addEventForm = document.getElementById("add-event-form");
  const feedback = document.getElementById("admin-feedback");
  const importShipmentsButton = document.getElementById("import-shipments-btn");
  const importEventsButton = document.getElementById("import-events-btn");
  const downloadTemplateButton = document.getElementById("download-excel-template-btn");
  const importShipmentsFile = document.getElementById("import-shipments-file");
  const importEventsFile = document.getElementById("import-events-file");

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return toJsonOrThrow(response);
  }

  function setFeedback(message, isError = false) {
    if (!feedback) return;
    feedback.textContent = message;
    feedback.className = `feedback ${isError ? "error" : "success"}`;
    window.OSLUI?.toast?.(message, isError);
  }

  function normalizeRowKeys(row) {
    const mapping = {
      date: "date",
      tracking: "tracking_number",
      trackingnumber: "tracking_number",
      tracking_number: "tracking_number",
      client: "client",
      client_name: "client",
      poids: "poids",
      weight: "poids",
      colis: "colis",
      parcel: "colis",
      parcels: "colis",
      envoi: "envoi",
      service: "envoi",
      frais: "frais",
      fee: "frais",
      fees: "frais",
      code: "code",
      statut: "code",
      status: "code",
      label: "label",
      libelle: "label",
      libellé: "label",
      location: "location",
      lieu: "location",
      details: "details",
      detail: "details",
      détail: "details",
      ts: "ts",
      event_time: "ts",
      date: "ts",
    };

    return Object.entries(row).reduce((acc, [key, value]) => {
      const normalizedKey = String(key)
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_");
      const mappedKey = mapping[normalizedKey] || normalizedKey;
      acc[mappedKey] = typeof value === "string" ? value.trim() : value;
      return acc;
    }, {});
  }

  async function parseExcelFile(file) {
    if (!window.XLSX) {
      throw new Error("Librairie Excel non chargée. Recharge la page puis réessaie.");
    }

    const buffer = await file.arrayBuffer();
    const workbook = window.XLSX.read(buffer, { type: "array" });
    const firstSheetName = workbook.SheetNames[0];
    if (!firstSheetName) {
      return [];
    }

    const worksheet = workbook.Sheets[firstSheetName];
    return window.XLSX.utils.sheet_to_json(worksheet, { defval: "" }).map(normalizeRowKeys);
  }

  async function importRows(rows, endpoint, buildPayload) {
    let successCount = 0;
    const errors = [];

    for (const [index, row] of rows.entries()) {
      const payload = buildPayload(row);
      try {
        await postJson(endpoint, payload);
        successCount += 1;
      } catch (err) {
        errors.push(`Ligne ${index + 2}: ${err.message}`);
      }
    }

    return { successCount, errors };
  }

  function requireFields(row, fields) {
    const missing = fields.filter((field) => !row[field]);
    if (missing.length) {
      throw new Error(`Champs manquants: ${missing.join(", ")}`);
    }
  }

  function downloadExcelTemplate() {
    if (!window.XLSX) {
      setFeedback("Librairie Excel non chargée. Recharge la page puis réessaie.", true);
      return;
    }

    const workbook = window.XLSX.utils.book_new();
    const shipmentsSheet = window.XLSX.utils.aoa_to_sheet([
      ["date", "tracking_number", "client", "poids", "colis", "envoi", "frais"],
      ["2026-04-04", "OSL-2026-0100", "Alice Export", 24.5, 6, "Express", 250000],
    ]);
    const eventsSheet = window.XLSX.utils.aoa_to_sheet([
      ["tracking_number", "code", "location", "details", "ts"],
      ["OSL-2026-0100", "IN_TRANSIT", "Dubaï", "En route vers hub", "2026-03-04T08:30:00Z"],
    ]);

    window.XLSX.utils.book_append_sheet(workbook, shipmentsSheet, "colis");
    window.XLSX.utils.book_append_sheet(workbook, eventsSheet, "evenements");
    window.XLSX.writeFile(workbook, "modele_import_osl.xlsx");
    setFeedback("Modèle Excel téléchargé: modele_import_osl.xlsx");
  }

  createShipmentForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = formToObject(createShipmentForm);
      const data = await postJson("/api/track", payload);
      setFeedback(`${data.message}: ${data.tracking_number}`);
      createShipmentForm.reset();
    } catch (err) {
      setFeedback(err.message, true);
    }
  });

  addEventForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = formToObject(addEventForm);
      const data = await postJson("/api/events", payload);
      setFeedback(data.message);
      addEventForm.reset();
    } catch (err) {
      setFeedback(err.message, true);
    }
  });

  importShipmentsButton?.addEventListener("click", () => {
    importShipmentsFile?.click();
  });

  importEventsButton?.addEventListener("click", () => {
    importEventsFile?.click();
  });

  downloadTemplateButton?.addEventListener("click", downloadExcelTemplate);

  importShipmentsFile?.addEventListener("change", async () => {
    const file = importShipmentsFile.files?.[0];
    if (!file) return;

    try {
      setFeedback("Import colis en cours...");
      const rows = await parseExcelFile(file);
      const { successCount, errors } = await importRows(rows, "/api/track", (row) => {
        requireFields(row, ["date", "tracking_number", "client", "poids", "colis", "envoi", "frais"]);
        return {
          date: row.date,
          tracking_number: row.tracking_number,
          client: row.client,
          poids: row.poids,
          colis: row.colis,
          envoi: row.envoi,
          frais: row.frais,
        };
      });

      if (errors.length) {
        setFeedback(`Import colis terminé: ${successCount} OK, ${errors.length} erreur(s). ${errors[0]}`, true);
      } else {
        setFeedback(`Import colis terminé: ${successCount} création(s).`);
      }
    } catch (err) {
      setFeedback(err.message, true);
    } finally {
      importShipmentsFile.value = "";
    }
  });

  importEventsFile?.addEventListener("change", async () => {
    const file = importEventsFile.files?.[0];
    if (!file) return;

    try {
      setFeedback("Import événements en cours...");
      const rows = await parseExcelFile(file);
      const { successCount, errors } = await importRows(rows, "/api/events", (row) => {
        requireFields(row, ["tracking_number", "code"]);
        return {
          tracking_number: row.tracking_number,
          code: String(row.code || "").toUpperCase(),
          label: row.label || "",
          location: row.location || "",
          details: row.details || "",
          ts: row.ts || "",
        };
      });

      if (errors.length) {
        setFeedback(`Import événements terminé: ${successCount} OK, ${errors.length} erreur(s). ${errors[0]}`, true);
      } else {
        setFeedback(`Import événements terminé: ${successCount} ajout(s).`);
      }
    } catch (err) {
      setFeedback(err.message, true);
    } finally {
      importEventsFile.value = "";
    }
  });
}

window.addEventListener("DOMContentLoaded", () => {
  initTrackPage();
  initAdminPage();
});
