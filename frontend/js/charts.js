/**
 * charts.js — Chart.js configuration and rendering
 * Manages Bar, Radar and Pie charts for the agriculture dashboard.
 */

// Chart colour palette (earthy greens)
const COLORS = {
  green:        'rgba(46, 125, 50, 0.8)',
  greenBorder:  'rgba(46, 125, 50, 1)',
  lime:         'rgba(104, 159, 56, 0.8)',
  limeBorder:   'rgba(104, 159, 56, 1)',
  amber:        'rgba(255, 160, 0, 0.8)',
  amberBorder:  'rgba(255, 160, 0, 1)',
  teal:         'rgba(0, 137, 123, 0.8)',
  tealBorder:   'rgba(0, 137, 123, 1)',
  brown:        'rgba(121, 85, 72, 0.8)',
  brownBorder:  'rgba(121, 85, 72, 1)',
  grid:         'rgba(0, 0, 0, 0.05)',
};

const PIE_COLORS = [
  'rgba(46, 125, 50, 0.85)',
  'rgba(104, 159, 56, 0.85)',
  'rgba(255, 160, 0, 0.85)',
  'rgba(121, 85, 72, 0.85)',
];

let barChart   = null;
let radarChart = null;
let pieChart   = null;

// ─── Common chart defaults ────────────────────────────────────────────────────

if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = "'Segoe UI', 'Roboto', sans-serif";
  Chart.defaults.color = '#4a4a4a';
}

// ─── Bar Chart — Yield Comparison ────────────────────────────────────────────

/**
 * Renders / updates the yield comparison bar chart.
 * @param {{ labels: string[], data: number[] }} yieldData
 */
export function renderBarChart(yieldData) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet');
    return;
  }
  const ctx = document.getElementById('barChart');
  if (!ctx) return;

  const chartData = {
    labels: yieldData.labels || ['Rice', 'Wheat', 'Maize', 'Soybean'],
    datasets: [{
      label: 'Predicted Yield (tons/hectare)',
      data: yieldData.data || [4.2, 3.8, 5.1, 2.9],
      backgroundColor: [COLORS.green, COLORS.lime, COLORS.amber, COLORS.teal],
      borderColor: [COLORS.greenBorder, COLORS.limeBorder, COLORS.amberBorder, COLORS.tealBorder],
      borderWidth: 2,
      borderRadius: 6,
      borderSkipped: false,
    }],
  };

  if (barChart) {
    barChart.data = chartData;
    barChart.update('active');
    return;
  }

  barChart = new Chart(ctx, {
    type: 'bar',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.parsed.y} tons/ha`,
          },
        },
        title: {
          display: true,
          text: 'Yield Comparison Across Crops',
          font: { size: 14, weight: '600' },
          padding: { bottom: 16 },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Yield (tons/hectare)' },
          grid: { color: COLORS.grid },
        },
        x: {
          grid: { display: false },
        },
      },
    },
  });
}

// ─── Radar Chart — Nutrient Analysis ─────────────────────────────────────────

/**
 * Renders / updates the soil nutrient radar chart.
 * @param {{ n: number, p: number, k: number, ph: number }} nutrients
 */
export function renderRadarChart(nutrients) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet');
    return;
  }
  const ctx = document.getElementById('radarChart');
  if (!ctx) return;

  // Normalise pH (0–14) to a 0–100 scale for visual consistency
  const phNorm = (nutrients.ph / 14) * 100;

  const chartData = {
    labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 'pH Level'],
    datasets: [
      {
        label: 'Your Soil',
        data: [nutrients.n, nutrients.p, nutrients.k, phNorm],
        backgroundColor: 'rgba(46, 125, 50, 0.2)',
        borderColor: COLORS.greenBorder,
        pointBackgroundColor: COLORS.greenBorder,
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: COLORS.greenBorder,
        borderWidth: 2,
      },
      {
        label: 'Optimal Range',
        // Mid-points of typical optimal ranges, scaled to 0–100:
        //   N: 80 kg/ha (range 60–100), P: 60 kg/ha (range 40–80),
        //   K: 70 kg/ha (range 50–90), pH: 6.5 → (6.5/14)*100 ≈ 46
        data: [80, 60, 70, 46],
        backgroundColor: 'rgba(104, 159, 56, 0.1)',
        borderColor: COLORS.limeBorder,
        borderDash: [6, 3],
        pointBackgroundColor: COLORS.limeBorder,
        pointBorderColor: '#fff',
        borderWidth: 2,
      },
    ],
  };

  if (radarChart) {
    radarChart.data = chartData;
    radarChart.update('active');
    return;
  }

  radarChart = new Chart(ctx, {
    type: 'radar',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
        title: {
          display: true,
          text: 'Soil Nutrient Analysis',
          font: { size: 14, weight: '600' },
          padding: { bottom: 16 },
        },
        tooltip: {
          callbacks: {
            label: ctx => {
              const val = ctx.parsed.r;
              if (ctx.label === 'pH Level') {
                return ` pH: ${((val / 100) * 14).toFixed(1)}`;
              }
              return ` ${ctx.dataset.label}: ${val}`;
            },
          },
        },
      },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 20, backdropColor: 'transparent' },
          grid: { color: COLORS.grid },
          angleLines: { color: COLORS.grid },
        },
      },
    },
  });
}

// ─── Pie Chart — Fertilizer Distribution ─────────────────────────────────────

/**
 * Renders / updates the fertilizer recommendation pie chart.
 * @param {{ labels: string[], data: number[] }} recData
 */
export function renderPieChart(recData) {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded yet');
    return;
  }
  const ctx = document.getElementById('pieChart');
  if (!ctx) return;

  const labels = recData.labels || ['Nitrogen', 'Phosphorus', 'Potassium', 'Organic'];
  const data   = recData.data   || [40, 25, 20, 15];

  const chartData = {
    labels,
    datasets: [{
      data,
      backgroundColor: PIE_COLORS,
      borderColor: '#fff',
      borderWidth: 3,
      hoverOffset: 8,
    }],
  };

  if (pieChart) {
    pieChart.data = chartData;
    pieChart.update('active');
    return;
  }

  pieChart = new Chart(ctx, {
    type: 'doughnut',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '60%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 16 } },
        title: {
          display: true,
          text: 'Fertilizer Recommendation Breakdown',
          font: { size: 14, weight: '600' },
          padding: { bottom: 16 },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed}%`,
          },
        },
      },
    },
  });
}
