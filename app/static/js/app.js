/**
 * app.js — Form hồ sơ + render bảng món + swap UI (Đăng - Tuần 10)
 *
 * Luồng chính (theo TASK_WEEK10.md):
 *   (1) Nhập hồ sơ → POST /api/targets → hiển thị BMR/TDEE/macro
 *   (2) Tạo thực đơn → POST /api/menu/generate → bảng món + radar
 *   (3) Thay món → POST /api/menu/swap → cập nhật 1 dòng + delta + radar
 */

import { apiTargets, apiGenerateMenu, apiSwapMenu, apiProfiles, apiSearchFoods } from './api.js';
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

// Tags
const conditionsTags = $('conditionsTags');
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

// Swap modal
const swapModal     = $('swapModal');
const swapSlotLabel = $('swapSlotLabel');
const swapFoodSearch= $('swapFoodSearch');
const swapDropdown  = $('swapDropdown');
const btnSwapConfirm= $('btnSwapConfirm');
const btnSwapCancel = $('btnSwapCancel');

let _swapSlot       = null;
let _swapSelectedId = null;

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
      items.delete(last);
      const tagEls = container.querySelectorAll('.tag-item');
      if (tagEls.length) tagEls[tagEls.length - 1].remove();
    }
  });

  return {
    getValues: () => [...items],
    setValues: (vals) => {
      items.clear();
      container.querySelectorAll('.tag-item').forEach(t => t.remove());
      vals.forEach(v => addTag(v));
    },
  };
}

// ---------------------------------------------------------------------------
// Build ProfileIn từ form
// ---------------------------------------------------------------------------

function parseCount(input, fallback = 0) {
  const v = parseInt(input.value, 10);
  return Number.isNaN(v) ? fallback : Math.max(0, v);
}

function readProfile() {
  return {
    name:        inpName.value.trim() || 'Người dùng',
    age:         parseInt(inpAge.value, 10) || 25,
    gender:      selGender.value,
    height_cm:   parseFloat(inpHeight.value) || 170,
    weight_kg:   parseFloat(inpWeight.value) || 65,
    activity_level: selActivity.value,
    goal:        selGoal.value,
    meal_counts: {
      breakfast: parseCount(mcBreakfast, 2),
      lunch:     parseCount(mcLunch, 2),
      dinner:    parseCount(mcDinner, 2),
      snack:     parseCount(mcSnack, 1),
    },
    medical_conditions: condCtrl.getValues(),
    allergies:          allergyCtrl.getValues(),
    dislikes:           dislikeCtrl.getValues(),
  };
}

function fillForm(preset) {
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
  condCtrl.setValues(preset.medical_conditions || []);
  allergyCtrl.setValues(preset.allergies || []);
  dislikeCtrl.setValues(preset.dislikes || []);
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

async function computeTargets() {
  const profile = readProfile();
  state.profile = profile;

  setLoading(btnTargets, true);
  try {
    const res = await apiTargets(profile);
    state.targets = res;
    renderTargetsBar(res);
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
  state.profile = readProfile();
  state.seed    = parseInt(inpSeed.value, 10) || 9001;

  setLoading(btnGenerate, true, 'Đang tính toán...');
  try {
    const res = await apiGenerateMenu(state.profile, state.seed, state.config);
    state.menu = res;
    state.foodIds = res.items.map(i => i.food_id);
    renderMenu(res);

    // Luôn làm mới targets tương ứng với profile hiện tại
    try {
      const tr = await apiTargets(state.profile);
      state.targets = tr;
      renderTargetsBar(tr);
    } catch (_) {
      // fallback dùng targets từ solver nếu apiTargets lỗi
      if (!state.targets) {
        state.targets = { bmr: 0, tdee: 0, targets: res.targets };
      }
    }

    const currentTargets = state.targets?.targets || res.targets;
    updateRadar(res.totals, currentTargets);
    updateProgressBars(res.totals, currentTargets, 'progressBars');

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
          ${icon} ${mealName}
        </span>
      </td>
      <td class="food-name-cell">
        <div class="food-name">${escHtml(item.name)}</div>
        <div class="food-id">${item.food_id}</div>
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
      <td>
        <button class="btn-swap" onclick="openSwap('${item.slot}', ${idx})"
                title="Thay món tại slot ${item.slot}">
          ↔ Thay
        </button>
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
    <td></td>
  `;

  // Violations
  renderViolations(menuData.violations);
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
// Swap
// ---------------------------------------------------------------------------

window.openSwap = function(slot, _idx) {
  _swapSlot = slot;
  _swapSelectedId = null;
  swapSlotLabel.textContent = slot;
  swapFoodSearch.value = '';
  swapDropdown.innerHTML = '';
  swapDropdown.style.display = 'none';
  btnSwapConfirm.disabled = true;
  swapModal.style.display = 'flex';
};

btnSwapCancel.addEventListener('click', () => { swapModal.style.display = 'none'; });
swapModal.addEventListener('click', e => { if (e.target === swapModal) swapModal.style.display = 'none'; });

// Food search trong modal
let _searchTimer = null;
swapFoodSearch.addEventListener('input', () => {
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(async () => {
    const q = swapFoodSearch.value.trim();
    if (!q) { swapDropdown.style.display = 'none'; return; }
    try {
      const foods = await apiSearchFoods(q, 15);
      renderFoodDropdown(foods);
    } catch (_) { /* ignore */ }
  }, 280);
});

function renderFoodDropdown(foods) {
  swapDropdown.innerHTML = '';
  if (!foods.length) { swapDropdown.style.display = 'none'; return; }
  foods.forEach(f => {
    const div = document.createElement('div');
    div.className = 'food-option';
    div.innerHTML = `
      <span>${escHtml(f.food_name)}</span>
      <span class="food-option-kcal">${f.calories.toFixed(0)} kcal</span>`;
    div.addEventListener('click', () => {
      _swapSelectedId = f.food_id;
      swapFoodSearch.value = f.food_name;
      swapDropdown.style.display = 'none';
      btnSwapConfirm.disabled = false;
    });
    swapDropdown.appendChild(div);
  });
  swapDropdown.style.display = 'block';
}

btnSwapConfirm.addEventListener('click', async () => {
  if (!_swapSlot || !state.profile || !state.foodIds.length) return;
  swapModal.style.display = 'none';
  setLoading(btnGenerate, true, 'Đang thay món...');
  try {
    const res = await apiSwapMenu(
      state.profile, state.foodIds, _swapSlot,
      _swapSelectedId, state.seed
    );
    // Patch state
    state.menu = { ...state.menu, ...res };
    state.foodIds = res.items.map(i => i.food_id);
    renderMenu(state.menu);
    updateRadar(res.totals, state.targets?.targets || res.targets);
    updateProgressBars(res.totals, state.targets?.targets || res.targets, 'progressBars');

    // Show delta
    const d = res.delta;
    const dCal = d.calories?.toFixed(0);
    toast(`Thay thành công! Δ Calo: ${dCal > 0 ? '+' : ''}${dCal} kcal`, 'success');
  } catch (err) {
    if (err.status === 501) {
      toast('Tính năng đổi món đang được hoàn thiện (Cương phụ trách)', 'info', 5000);
    } else {
      toast(`Lỗi thay món: ${err.message}`, 'error');
    }
  } finally {
    setLoading(btnGenerate, false, '⚡ Tạo thực đơn');
  }
});

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
inpSeed.addEventListener('change', () => { state.seed = parseInt(inpSeed.value, 10) || 9001; });

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

let condCtrl, allergyCtrl, dislikeCtrl;

document.addEventListener('DOMContentLoaded', () => {
  condCtrl    = createTagsInput(conditionsTags);
  allergyCtrl = createTagsInput(allergyTags);
  dislikeCtrl = createTagsInput(dislikeTags);

  initCharts();
  loadPresets();

  // Ẩn menu section cho đến khi có menu
  menuSection.style.display = 'none';
  targetsBar.style.display  = 'none';
});
