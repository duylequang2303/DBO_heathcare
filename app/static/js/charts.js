/**
 * charts.js — Radar dinh dưỡng + thanh tiến độ (Đăng - Tuần 10)
 *
 * Phụ thuộc: Chart.js (CDN, loaded in index.html)
 *
 * Export:
 *   initCharts()           — khởi tạo radar canvas
 *   updateRadar(totals, targets)  — cập nhật radar từ data
 *   updateProgressBars(totals, targets, containerId)
 */

/** @type {Chart|null} */
let _radarChart = null;

/**
 * Tỷ lệ tolerance theo AGENTS.md:
 *   calories  ±10%
 *   protein   ±15%
 *   carbs     ±15%
 *   fat       ±20%
 *   fiber     ±30%
 */
const TOLERANCE = {
  calories:  0.10,
  protein_g: 0.15,
  carbs_g:   0.15,
  fat_g:     0.20,
  fiber_g:   0.30,
};

const NUTRIENT_LABELS = {
  calories:  'Năng lượng',
  protein_g: 'Protein',
  carbs_g:   'Carbs',
  fat_g:     'Chất béo',
  fiber_g:   'Chất xơ',
  sodium_mg: 'Natri',
};

const NUTRIENT_UNITS = {
  calories:  'kcal',
  protein_g: 'g',
  carbs_g:   'g',
  fat_g:     'g',
  fiber_g:   'g',
  sodium_mg: 'mg',
};

/**
 * Tính % đạt target (capped 0–150 để radar không bị quá méo)
 */
function pctOfTarget(actual, target) {
  if (!target || target === 0) return 0;
  return Math.min(150, Math.round((actual / target) * 100));
}

/**
 * Xác định class CSS cho progress bar dựa trên tỷ lệ % và tolerance.
 */
function progressClass(pct, key) {
  const tol = (TOLERANCE[key] ?? 0.15) * 100;
  if (pct < (100 - tol)) return 'warn';
  if (pct > (100 + tol)) return 'over';
  return 'ok';
}

// ---------------------------------------------------------------------------
// Radar Chart
// ---------------------------------------------------------------------------

const RADAR_KEYS = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g'];

/**
 * Khởi tạo Chart.js radar trên canvas #nutrientRadar.
 * Gọi một lần khi DOM ready.
 */
export function initCharts() {
  const canvas = document.getElementById('nutrientRadar');
  if (!canvas) return;

  // Destroy nếu đã tồn tại (hot-reload safe)
  if (_radarChart) { _radarChart.destroy(); _radarChart = null; }

  const ctx = canvas.getContext('2d');
  _radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: RADAR_KEYS.map(k => NUTRIENT_LABELS[k] || k),
      datasets: [
        {
          label: 'Đạt được (%)',
          data: RADAR_KEYS.map(() => 0),
          backgroundColor: 'rgba(59,130,246,0.18)',
          borderColor: 'rgba(59,130,246,0.8)',
          borderWidth: 2,
          pointBackgroundColor: '#3b82f6',
          pointBorderColor: '#fff',
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: 'Mục tiêu (100%)',
          data: RADAR_KEYS.map(() => 100),
          backgroundColor: 'rgba(255,255,255,0.02)',
          borderColor: 'rgba(255,255,255,0.15)',
          borderWidth: 1,
          borderDash: [4, 4],
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 600, easing: 'easeInOutQuart' },
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11 },
            boxWidth: 12,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(17,24,39,0.95)',
          borderColor: 'rgba(255,255,255,0.1)',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.raw}%`,
          },
        },
      },
      scales: {
        r: {
          min: 0, max: 130,
          ticks: {
            stepSize: 25,
            color: '#475569',
            backdropColor: 'transparent',
            font: { size: 10 },
          },
          grid: { color: 'rgba(255,255,255,0.06)' },
          angleLines: { color: 'rgba(255,255,255,0.06)' },
          pointLabels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 11, weight: '500' },
          },
        },
      },
    },
  });
}

/**
 * Cập nhật radar với totals và targets thực từ solver.
 * @param {Object} totals   — {calories, protein_g, ...}
 * @param {Object} targets  — {calories, protein_g, ...}
 */
export function updateRadar(totals, targets) {
  if (!_radarChart) return;
  const pcts = RADAR_KEYS.map(k => pctOfTarget(totals[k] ?? 0, targets[k] ?? 1));
  _radarChart.data.datasets[0].data = pcts;
  _radarChart.update();
}

// ---------------------------------------------------------------------------
// Progress bars
// ---------------------------------------------------------------------------

/**
 * Render thanh tiến độ vào container element.
 * @param {Object} totals
 * @param {Object} targets
 * @param {string} containerId — id của div chứa progress bars
 */
export function updateProgressBars(totals, targets, containerId = 'progressBars') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const keys = ['calories', 'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'sodium_mg'];
  container.innerHTML = '';

  keys.forEach(key => {
    const actual = totals[key] ?? 0;
    const target = targets[key] ?? 0;
    if (!target) return;

    const pct = pctOfTarget(actual, target);
    const cls = key === 'sodium_mg'
      ? (actual > target ? 'over' : 'ok')  // sodium: chỉ cần không vượt
      : progressClass(pct, key);
    const barPct = Math.min(pct, 100);     // bar không vượt 100% visually
    const unit = NUTRIENT_UNITS[key] || '';
    const label = NUTRIENT_LABELS[key] || key;

    const item = document.createElement('div');
    item.className = 'progress-item';
    item.innerHTML = `
      <span class="progress-label" title="${actual.toFixed(1)}${unit} / ${target.toFixed(1)}${unit}">
        ${label}
      </span>
      <div class="progress-track">
        <div class="progress-fill ${cls}" style="width:${barPct}%"></div>
      </div>
      <span class="progress-pct ${cls}">${pct}%</span>
    `;
    container.appendChild(item);
  });
}
