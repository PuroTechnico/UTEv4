// ============================================================
// Auto Dark/Light Mode
// ============================================================

const prefersDark =
  window.matchMedia &&
  window.matchMedia("(prefers-color-scheme: dark)").matches;

const baseGridColor = prefersDark ? "#444" : "#ccc";
const baseTextColor = prefersDark ? "#e6e6e6" : "#222";


// ============================================================
// Weather Model Chart
// ============================================================

function renderWeatherModelChart(probCurve) {
  const el = document.getElementById("weatherModelChart");
  if (!el) return;

  const ctx = el.getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: [...Array(probCurve.length).keys()],
      datasets: [
        {
          label: "Prob > Strike",
          data: probCurve,
          borderColor: "#3a7afe",
          backgroundColor: "rgba(58,122,254,0.2)",
          tension: 0.25,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: baseGridColor },
          ticks: { color: baseTextColor },
        },
        y: {
          grid: { color: baseGridColor },
          ticks: { color: baseTextColor },
        },
      },
    },
  });
}


// ============================================================
// Crypto Volatility Sparklines
// ============================================================

function renderSparkline(asset, sparklineData) {
  const el = document.getElementById(`spark_${asset}`);
  if (!el) return;

  const ctx = el.getContext("2d");

  new Chart(ctx, {
    type: "line",
    data: {
      labels: [...Array(sparklineData.length).keys()],
      datasets: [
        {
          data: sparklineData,
          borderColor: "#ffb74d",
          backgroundColor: "rgba(255,183,77,0.15)",
          tension: 0.25,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { display: false },
        y: { display: false },
      },
      elements: {
        point: { radius: 0 },
      },
    },
  });
}


// ============================================================
// Heartbeat Timeline Chart
// ============================================================

function renderHeartbeatChart(timestamps, statuses) {
  const el = document.getElementById("heartbeatChart");
  if (!el) return;

  const ctx = el.getContext("2d");

  const numeric = statuses.map((s) => {
    if (s === "OK") return 2;
    if (s === "WARN") return 1;
    if (s === "ERROR") return 0;
    return -1;
  });

  new Chart(ctx, {
    type: "line",
    data: {
      labels: timestamps,
      datasets: [
        {
          data: numeric,
          borderColor: "#4caf50",
          backgroundColor: "rgba(76,175,80,0.2)",
          stepped: true,
        },
      ],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { color: baseGridColor },
          ticks: { color: baseTextColor, maxTicksLimit: 5 },
        },
        y: {
          grid: { color: baseGridColor },
          ticks: {
            color: baseTextColor,
            callback: function (v) {
              if (v === 2) return "OK";
              if (v === 1) return "WARN";
              if (v === 0) return "ERROR";
              return "";
            },
          },
          min: -0.5,
          max: 2.5,
        },
      },
    },
  });
}


// ============================================================
// Bootstrapping — called from inline script in HTML
// ============================================================

window.DashboardCharts = {
  renderWeatherModelChart,
  renderSparkline,
  renderHeartbeatChart,
};
