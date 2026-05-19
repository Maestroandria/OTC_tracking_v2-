(function () {
  function parseChartData() {
    const node = document.getElementById("super-admin-chart-data");
    if (!node || !node.textContent) return null;
    try {
      return JSON.parse(node.textContent);
    } catch (error) {
      console.error("Invalid chart payload", error);
      return null;
    }
  }

  function createPalette(size) {
    const base = [
      "#1d9bf0",
      "#0ea5e9",
      "#0284c7",
      "#38bdf8",
      "#06b6d4",
      "#2dd4bf",
      "#84cc16",
      "#f59e0b",
      "#f97316",
      "#ef4444",
      "#a855f7",
      "#6366f1",
    ];
    const colors = [];
    for (let i = 0; i < size; i += 1) {
      colors.push(base[i % base.length]);
    }
    return colors;
  }

  function drawPieChart(canvasId, labels, values) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const safeValues = values.map((value) => Math.max(0, Number(value) || 0));
    const total = safeValues.reduce((acc, value) => acc + value, 0);

    const dpi = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 480;
    const cssHeight = canvas.clientHeight || 280;
    canvas.width = Math.floor(cssWidth * dpi);
    canvas.height = Math.floor(cssHeight * dpi);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpi, dpi);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    if (!total) {
      ctx.fillStyle = "#6b7280";
      ctx.font = "600 14px Segoe UI, sans-serif";
      ctx.fillText("Aucune donnée à afficher", 16, 28);
      return;
    }

    const colors = createPalette(labels.length);
    const centerX = Math.min(cssWidth * 0.35, 165);
    const centerY = cssHeight * 0.5;
    const radius = Math.min(cssHeight * 0.36, 95);

    let angle = -Math.PI / 2;
    safeValues.forEach((value, index) => {
      const sliceAngle = (value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, angle, angle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = colors[index];
      ctx.fill();
      angle += sliceAngle;
    });

    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.53, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();

    ctx.fillStyle = "#0f172a";
    ctx.font = "700 13px Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${labels.length} catégories`, centerX, centerY - 2);
    ctx.font = "600 12px Segoe UI, sans-serif";
    ctx.fillStyle = "#64748b";
    ctx.fillText("Répartition", centerX, centerY + 16);

    const legendX = Math.max(centerX + radius + 24, cssWidth * 0.55);
    let legendY = 26;
    labels.forEach((label, index) => {
      const value = safeValues[index];
      const pct = total ? ((value / total) * 100).toFixed(1) : "0.0";

      ctx.fillStyle = colors[index];
      ctx.fillRect(legendX, legendY - 10, 10, 10);

      ctx.fillStyle = "#0f172a";
      ctx.font = "600 12px Segoe UI, sans-serif";
      const safeLabel = String(label || "-").slice(0, 22);
      ctx.fillText(`${safeLabel} (${pct}%)`, legendX + 16, legendY - 1);

      legendY += 18;
      if (legendY > cssHeight - 12) {
        legendY = cssHeight - 12;
      }
    });
    ctx.textAlign = "start";
  }

  function drawHorizontalBarChart(canvasId, labels, values, valueSuffix) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const safeValues = values.map((value) => Math.max(0, Number(value) || 0));
    const maxValue = Math.max(...safeValues, 0);

    const dpi = window.devicePixelRatio || 1;
    const cssWidth = canvas.clientWidth || 480;
    const cssHeight = canvas.clientHeight || 280;
    canvas.width = Math.floor(cssWidth * dpi);
    canvas.height = Math.floor(cssHeight * dpi);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpi, dpi);
    ctx.clearRect(0, 0, cssWidth, cssHeight);

    if (!labels.length || maxValue <= 0) {
      ctx.fillStyle = "#6b7280";
      ctx.font = "600 14px Segoe UI, sans-serif";
      ctx.fillText("Aucune donnée à afficher", 16, 28);
      return;
    }

    const top = 22;
    const left = 16;
    const right = cssWidth - 16;
    const barAreaWidth = Math.max(120, right - left - 150);
    const barHeight = 14;
    const rowGap = 12;
    const maxRows = Math.max(1, Math.min(labels.length, Math.floor((cssHeight - top) / (barHeight + rowGap))));
    const palette = createPalette(maxRows);

    ctx.font = "600 12px Segoe UI, sans-serif";
    for (let i = 0; i < maxRows; i += 1) {
      const label = String(labels[i] || "-").slice(0, 26);
      const value = safeValues[i];
      const y = top + i * (barHeight + rowGap);

      ctx.fillStyle = "#475569";
      ctx.fillText(label, left, y - 4);

      ctx.fillStyle = "#e2e8f0";
      ctx.fillRect(left, y, barAreaWidth, barHeight);

      const width = maxValue ? (value / maxValue) * barAreaWidth : 0;
      ctx.fillStyle = palette[i];
      ctx.fillRect(left, y, width, barHeight);

      ctx.fillStyle = "#0f172a";
      const formattedValue = Number.isFinite(value) ? value.toFixed(2).replace(/\.00$/, "") : "0";
      ctx.fillText(`${formattedValue}${valueSuffix || ""}`, left + barAreaWidth + 10, y + 11);
    }
  }

  function boot() {
    const payload = parseChartData();
    if (!payload) return;

    const statusRows = Array.isArray(payload.status_breakdown) ? payload.status_breakdown : [];
    drawPieChart(
      "status-pie-chart",
      statusRows.map((row) => row.label || "Sans statut"),
      statusRows.map((row) => row.count || 0)
    );

    const serviceRows = Array.isArray(payload.amount_by_service) ? payload.amount_by_service : [];
    drawPieChart(
      "service-pie-chart",
      serviceRows.map((row) => row.service || "Service"),
      serviceRows.map((row) => row.amount || 0)
    );

    const topClientsRows = Array.isArray(payload.top_clients) ? payload.top_clients : [];
    drawHorizontalBarChart(
      "top-clients-bar-chart",
      topClientsRows.map((row) => row.client || "Client"),
      topClientsRows.map((row) => row.amount || 0),
      " Ar"
    );

    const avgRows = Array.isArray(payload.avg_weight_by_client) ? payload.avg_weight_by_client : [];
    drawHorizontalBarChart(
      "avg-weight-bar-chart",
      avgRows.map((row) => row.client || "Client"),
      avgRows.map((row) => row.avg_weight || 0),
      " kg"
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
