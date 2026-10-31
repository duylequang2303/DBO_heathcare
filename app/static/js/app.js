/**
 * app.js — Form hồ sơ + render bảng món (Đăng - Tuần 10)
 *
 * Luồng chính (theo TASK_WEEK10.md):
 *   (1) Nhập hồ sơ → POST /api/targets → hiển thị BMR/TDEE/macro
 *   (2) Tạo thực đơn → POST /api/menu/generate → bảng món + radar
 */

import { apiTargets, apiGenerateMenu, apiProfiles, apiSwapMenu } from './api.js';
import { initCharts, updateRadar, updateProgressBars } from './charts.js';

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

const state = {
  profile: null,          // ProfileIn object hiện tại
  targets: null,          // TargetsOut từ /api/targets
  menu: null,             // MenuOut từ /api/menu/generate
  foodIds: [],            // food_ids hiện tại của menu
  config: 'web',          // 'smoke' | 'web' | 'full'
  seed: 9001,
};

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------

const $ = id => document.getElementById(id);

// ---- Form ----
const formProfile   = $('formProfile');
const inpName       = $('inpName');
const inpAge        = $('inpAge');
const selGender     = $('selGender');
const inpHeight     = $('inpHeight');
const inpWeight     = $('inpWeight');
const selActivity   = $('selActivity');
const selGoal       = $('selGoal');
const inpSeed       = $('inpSeed');

// Meal counts
const mcBreakfast = $('mcBreakfast');
const mcLunch     = $('mcLunch');
const mcDinner    = $('mcDinner');
const mcSnack     = $('mcSnack');

// Tags & Medical
const selMedicalCondition = $('medicalCondition');
const allergyTags    = $('allergyTags');
const dislikeTags    = $('dislikeTags');

// Buttons
const btnLoadP1    = $('btnLoadP1');
const btnLoadP2    = $('btnLoadP2');
const btnLoadP3    = $('btnLoadP3');
const btnTargets   = $('btnTargets');
const btnGenerate  = $('btnGenerate');

// Config buttons
const cfgSmoke = $('cfgSmoke');
const cfgWeb   = $('cfgWeb');
const cfgFull  = $('cfgFull');

// Output areas
const targetsBar    = $('targetsBar');
const menuSection   = $('menuSection');
const menuTableBody = $('menuTableBody');
const totalRow      = $('totalRow');
const fitnessEl     = $('fitnessScore');
const violationsEl  = $('violationsList');
const diversityEl   = $('diversityPct');
const runtimeEl     = $('runtimeSec');

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------

function toast(msg, type = 'info', duration = 4000) {
  const container = document.querySelector('.toast-container') || (() => {
    const el = document.createElement('div');
    el.className = 'toast-container';
    document.body.appendChild(el);
    return el;
  })();
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => t.remove(), duration);
}

// ---------------------------------------------------------------------------
// Tags helper
// ---------------------------------------------------------------------------

function createTagsInput(container) {
  const items = new Set();
  const input = container.querySelector('.tags-input');

  function addTag(val) {
    val = val.trim().toLowerCase();
    if (!val || items.has(val)) return;
    items.add(val);
    invalidateTargets();

    const tag = document.createElement('span');
    tag.className = 'tag-item';
    tag.textContent = val;

    const removeBtn = document.createElement('span');
    removeBtn.className = 'tag-remove';
    removeBtn.textContent = '✕';
    removeBtn.dataset.val = val;
    removeBtn.addEventListener('click', () => {
      items.delete(val);
      tag.remove();
      invalidateTargets();
      input.focus();
    });

    tag.appendChild(removeBtn);
    container.insertBefore(tag, input);
    input.value = '';
  }

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') { e.preventDefault(); addTag(input.value); }
    if (e.key === 'Backspace' && !input.value && items.size) {
      const last = [...items].at(-1);
      const removeBtn = [...container.querySelectorAll('.tag-remove')]
        .find(button => button.dataset.val === last);
      removeBtn?.click();
    }
  });

  return {
    getValues: () => [...items],
    setValues: (vals) => {
      items.clear();
      invalidateTargets();
      container.querySelectorAll('.tag-item').forEach(t => t.remove());
      vals.forEach(v => addTag(v));
    },
  };
}

// ---------------------------------------------------------------------------
// Build ProfileIn từ form
// ---------------------------------------------------------------------------

function parseCount(input) {
  const v = parseInt(input.value, 10);
  return Number.isNaN(v) ? 1 : v;
}

function readProfile() {
  const condVal = selMedicalCondition ? selMedicalCondition.value : '';
  return {
    name:        inpName.value.trim() || 'Người dùng',
    age:         parseInt(inpAge.value, 10) || 25,
    gender:      selGender.value,
    height_cm:   parseFloat(inpHeight.value) || 170,
    weight_kg:   parseFloat(inpWeight.value) || 65,
    activity_level: selActivity.value,
    goal:        selGoal.value,
    meal_counts: {
      breakfast: parseCount(mcBreakfast),
      lunch:     parseCount(mcLunch),
      dinner:    parseCount(mcDinner),
      snack:     parseCount(mcSnack),
    },
    medical_conditions: condVal ? [condVal] : [],
    allergies:          allergyCtrl ? allergyCtrl.getValues() : [],
    dislikes:           dislikeCtrl ? dislikeCtrl.getValues() : [],
  };
}

function fillForm(preset) {
  invalidateTargets();
  inpName.value    = preset.name || '';
  inpAge.value     = preset.age || '';
  selGender.value  = preset.gender || 'male';
  inpHeight.value  = preset.height_cm || '';
  inpWeight.value  = preset.weight_kg || '';
  selActivity.value = preset.activity_level || 'MODERATE';
  selGoal.value     = preset.goal || 'MAINTAIN';
  const mc = preset.meal_counts || {};
  mcBreakfast.value = mc.breakfast ?? 2;
  mcLunch.value     = mc.lunch ?? 2;
  mcDinner.value    = mc.dinner ?? 2;
  mcSnack.value     = mc.snack ?? 1;

  if (selMedicalCondition) {
    const conds = preset.medical_conditions || [];
    if (conds.includes('hypertension') || conds.includes('tăng huyết áp')) {
      selMedicalCondition.value = 'hypertension';
    } else if (conds.includes('diabetes') || conds.includes('tiểu đường') || conds.includes('đái tháo đường')) {
      selMedicalCondition.value = 'diabetes';
    } else {
      selMedicalCondition.value = '';
    }
  }

  if (allergyCtrl) allergyCtrl.setValues(preset.allergies || []);
  if (dislikeCtrl) dislikeCtrl.setValues(preset.dislikes || []);
}

// ---------------------------------------------------------------------------
// Config buttons
// ---------------------------------------------------------------------------

function setConfig(cfg) {
  state.config = cfg;
  [cfgSmoke, cfgWeb, cfgFull].forEach(b => b.classList.remove('active'));
  $(`cfg${cfg.charAt(0).toUpperCase() + cfg.slice(1)}`).classList.add('active');
}

cfgSmoke.addEventListener('click', () => setConfig('smoke'));
cfgWeb.addEventListener('click',   () => setConfig('web'));
cfgFull.addEventListener('click',  () => setConfig('full'));
setConfig('web');

// ---------------------------------------------------------------------------
// Targets
// ---------------------------------------------------------------------------

let targetsVersion = 0;

function invalidateTargets() {
  targetsVersion += 1;
  state.targets = null;
  targetsBar.style.display = 'none';
  targetsBar.innerHTML = '';
}

async function refreshTargets(profile) {
  invalidateTargets();
  const version = targetsVersion;
  const res = await apiTargets(profile);
  // Ignore responses for a profile that was edited while the request ran.
  if (version !== targetsVersion) return;
  state.targets = res;
  renderTargetsBar(res);
}

async function computeTargets() {
  const profile = readProfile();
  state.profile = profile;

  setLoading(btnTargets, true);
  try {
    await refreshTargets(profile);
    toast('Đã tính mục tiêu dinh dưỡng', 'success');
  } catch (err) {
    toast(`Lỗi: ${err.message}`, 'error');
  } finally {
    setLoading(btnTargets, false);
  }
}

function renderTargetsBar(res) {
  const t = res.targets;
  targetsBar.innerHTML = `
    <div class="target-chip">
      <span class="target-chip-label">BMR</span>
      <span class="target-chip-value">${res.bmr.toFixed(0)}</span>
      <span class="target-chip-unit">kcal</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">TDEE</span>
      <span class="target-chip-value">${res.tdee.toFixed(0)}</span>
      <span class="target-chip-unit">kcal</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Calo mục tiêu</span>
      <span class="target-chip-value">${(t.calories||0).toFixed(0)}</span>
      <span class="target-chip-unit">kcal</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Protein</span>
      <span class="target-chip-value">${(t.protein_g||0).toFixed(0)}</span>
      <span class="target-chip-unit">g</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Carbs</span>
      <span class="target-chip-value">${(t.carbs_g||0).toFixed(0)}</span>
      <span class="target-chip-unit">g</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Chất béo</span>
      <span class="target-chip-value">${(t.fat_g||0).toFixed(0)}</span>
      <span class="target-chip-unit">g</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Chất xơ</span>
      <span class="target-chip-value">${(t.fiber_g||0).toFixed(0)}</span>
      <span class="target-chip-unit">g</span>
    </div>
    <div class="target-chip">
      <span class="target-chip-label">Natri</span>
      <span class="target-chip-value">${(t.sodium_mg||0).toFixed(0)}</span>
      <span class="target-chip-unit">mg</span>
    </div>
  `;
  targetsBar.style.display = 'flex';
}

// ---------------------------------------------------------------------------
// Generate menu
// ---------------------------------------------------------------------------

async function generateMenu() {
  const profile = readProfile();
  state.profile = profile;
  state.seed    = parseInt(inpSeed.value, 10) || 9001;
  const { seed, config } = state;

  setLoading(btnGenerate, true, 'Đang tính toán...');
  try {
    try {
      await refreshTargets(profile);
    } catch (_) {
      toast('Không thể làm mới mục tiêu dinh dưỡng', 'info');
    }
    const res = await apiGenerateMenu(profile, seed, config);
    state.menu = res;
    state.foodIds = res.items.map(i => i.food_id);
    renderMenu(res);

    updateRadar(res.totals, res.targets);
    updateProgressBars(res.totals, res.targets, 'progressBars');

    menuSection.style.display = 'block';
    menuSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    toast(`Thực đơn đã tạo — Fitness: ${res.fitness}`, 'success');
  } catch (err) {
    toast(`Lỗi tạo thực đơn: ${err.message}`, 'error');
  } finally {
    setLoading(btnGenerate, false, '⚡ Tạo thực đơn');
  }
}

// ---------------------------------------------------------------------------
// Render menu table
// ---------------------------------------------------------------------------

const MEAL_ICONS = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍎' };
const MEAL_LABELS = { breakfast: 'Sáng', lunch: 'Trưa', dinner: 'Tối', snack: 'Phụ' };

function renderMenu(menuData) {
  // Stats
  if (fitnessEl) fitnessEl.innerHTML = `
    <span class="fitness-score">
      <span class="fitness-num">${menuData.fitness.toFixed(1)}</span>
      <span class="fitness-label">/ 100</span>
    </span>`;
  if (diversityEl) diversityEl.textContent = `Đa dạng: ${menuData.diversity_pct}%`;
  if (runtimeEl) runtimeEl.textContent = `⏱ ${menuData.runtime_s}s`;

  // Table rows
  menuTableBody.innerHTML = '';
  const items = menuData.items;

  items.forEach((item, idx) => {
    const mealName = item.slot.split('_')[0];
    const icon = MEAL_ICONS[mealName] || '🍽';
    const tr = document.createElement('tr');
    tr.id = `menuRow-${idx}`;
    tr.dataset.slot = item.slot;
    tr.dataset.foodId = item.food_id;
    tr.innerHTML = `
      <td>
        <span class="meal-badge ${mealName}">
          ${icon} ${MEAL_LABELS[mealName] || mealName}
        </span>
      </td>
      <td class="food-name-cell">
        <div class="food-name">${escHtml(item.name_vi || item.name)}</div>
      </td>
      <td class="portion-col">
        <span class="portion-raw">${item.portion_g.toFixed(1)}g</span>
        <span class="portion-sep">→</span>
        <span class="portion-rounded">${item.portion_g_rounded}g</span>
      </td>
      <td class="num-cell num-highlight">${item.macros.calories.toFixed(0)}</td>
      <td class="num-cell">${item.macros.protein_g.toFixed(1)}</td>
      <td class="num-cell">${item.macros.carbs_g.toFixed(1)}</td>
      <td class="num-cell">${item.macros.fat_g.toFixed(1)}</td>
      <td class="num-cell">${item.macros.fiber_g.toFixed(1)}</td>
      <td class="num-cell">${item.macros.sodium_mg.toFixed(0)}</td>
      <td style="text-align:center">
        <button class="btn-swap" data-slot="${item.slot}" type="button">🔄 Đổi món</button>
      </td>
    `;
    menuTableBody.appendChild(tr);
  });

  // Totals row
  const t = menuData.totals;
  totalRow.innerHTML = `
    <td colspan="2" style="font-weight:700;color:var(--text-2)">Tổng ngày</td>
    <td>—</td>
    <td class="num-cell num-highlight">${t.calories.toFixed(0)}</td>
    <td class="num-cell">${t.protein_g.toFixed(1)}</td>
    <td class="num-cell">${t.carbs_g.toFixed(1)}</td>
    <td class="num-cell">${t.fat_g.toFixed(1)}</td>
    <td class="num-cell">${t.fiber_g.toFixed(1)}</td>
    <td class="num-cell">${t.sodium_mg.toFixed(0)}</td>
    <td>—</td>
  `;

  // Violations
  renderViolations(menuData.violations);

  // Attach swap handlers
  menuTableBody.querySelectorAll('.btn-swap').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const slot = btn.dataset.slot;
      await handleSwap(slot, btn);
    });
  });
}

async function handleSwap(slot, btn) {
  if (!state.menu || !state.profile) {
    toast('Chưa có thực đơn để đổi món', 'error');
    return;
  }
  const originalText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '⏳ Đang đổi...';

  try {
    const foodIds = state.menu.items.map(i => i.food_id);
    const oldPortionsG = state.menu.items.map(i => i.portion_g);
    const res = await apiSwapMenu(state.profile, foodIds, slot, null, state.seed, oldPortionsG);

    state.menu = res;
    state.foodIds = res.items.map(i => i.food_id);

    renderMenu(res);
    if (state.targets) {
      updateRadar(res.totals, state.targets);
      updateProgressBars(res.totals, state.targets, 'progressBars');
    }

    const dCal = res.delta?.calories ?? 0;
    const sign = dCal >= 0 ? '+' : '';
    toast(`Đã đổi món tại slot ${slot} (Δ Calo: ${sign}${dCal.toFixed(0)} kcal)`, 'success');
  } catch (err) {
    toast(`Lỗi đổi món: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
}

function renderViolations(violations) {
  if (!violationsEl) return;
  if (!violations || violations.length === 0) {
    violationsEl.innerHTML = `<div class="toast success" style="animation:none">✅ Không có vi phạm ràng buộc</div>`;
    return;
  }
  violationsEl.innerHTML = violations.map(v => `
    <div class="violation-badge">
      <span class="v-icon">⚠️</span>
      <span>${escHtml(v)}</span>
    </div>`).join('');
}

// ---------------------------------------------------------------------------
// Preset profiles
// ---------------------------------------------------------------------------

async function loadPresets() {
  try {
    const profiles = await apiProfiles();
    btnLoadP1.addEventListener('click', () => { fillForm(profiles.p1); toast('Đã điền hồ sơ P1 — Duy', 'info'); });
    btnLoadP2.addEventListener('click', () => { fillForm(profiles.p2); toast('Đã điền hồ sơ P2 — Lan', 'info'); });
    btnLoadP3.addEventListener('click', () => { fillForm(profiles.p3); toast('Đã điền hồ sơ P3 — Minh', 'info'); });
  } catch (_) {
    // Nếu API chưa sẵn sàng, preset hoạt động offline với default data
    btnLoadP1.addEventListener('click', () => fillForm({
      name:'Duy', age:22, gender:'male', height_cm:170, weight_kg:65,
      activity_level:'MODERATE', goal:'MAINTAIN',
      meal_counts:{breakfast:2,lunch:2,dinner:2,snack:1},
      medical_conditions:['healthy'], allergies:[], dislikes:[]
    }));
  }
}

// ---------------------------------------------------------------------------
// Loading state helper
// ---------------------------------------------------------------------------

function setLoading(btn, loading, originalText) {
  if (loading) {
    btn.disabled = true;
    btn._original = btn.innerHTML;
    btn.innerHTML = `<div class="spinner"></div><span>${originalText || 'Đang xử lý...'}</span>`;
  } else {
    btn.disabled = false;
    btn.innerHTML = btn._original || originalText || btn.innerHTML;
  }
}

// ---------------------------------------------------------------------------
// Escape HTML
// ---------------------------------------------------------------------------

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ---------------------------------------------------------------------------
// Wire up events
// ---------------------------------------------------------------------------

btnTargets.addEventListener('click', computeTargets);
btnGenerate.addEventListener('click', generateMenu);
formProfile.addEventListener('input', invalidateTargets);
formProfile.addEventListener('change', invalidateTargets);
inpSeed.addEventListener('change', () => { state.seed = parseInt(inpSeed.value, 10) || 9001; });

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

let allergyCtrl, dislikeCtrl;

document.addEventListener('DOMContentLoaded', async () => {
  allergyCtrl = createTagsInput(allergyTags);
  dislikeCtrl = createTagsInput(dislikeTags);

  initCharts();
  await loadPresets();

  // Ẩn menu section cho đến khi có menu
  menuSection.style.display = 'none';
  targetsBar.style.display  = 'none';

  const params = new URLSearchParams(window.location.search);
  if (params.get('auto') === 'p1') {
    btnLoadP1.click();
    setConfig('smoke');
    await computeTargets();
    await generateMenu();
    document.body.classList.add('ready-screenshot');
  }
});
