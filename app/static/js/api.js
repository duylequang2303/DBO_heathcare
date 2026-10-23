/**
 * api.js — Tầng giao tiếp với FastAPI backend (Đăng - Tuần 10)
 *
 * Tất cả fetch calls tập trung ở đây.
 * Không có business logic — chỉ wrap HTTP.
 */

const BASE = '';  // cùng origin (một cổng)

/**
 * Tiện ích fetch JSON — throw Error với message rõ ràng khi thất bại.
 * @param {string} url
 * @param {RequestInit} options
 * @returns {Promise<any>}
 */
async function apiFetch(url, options = {}) {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (Array.isArray(body.detail)) {
        detail = body.detail
          .map(d => `${d.loc?.slice(-1)[0] || 'trường'}: ${d.msg}`)
          .join('; ');
      } else if (typeof body.detail === 'string') {
        detail = body.detail;
      } else if (body.detail) {
        detail = JSON.stringify(body.detail);
      }
    } catch (_) { /* ignore */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

// ---- Health ----------------------------------------------------------------

export async function apiHealth() {
  return apiFetch('/api/health');
}

// ---- Profiles presets -------------------------------------------------------

export async function apiProfiles() {
  return apiFetch('/api/profiles');
}

// ---- Targets ---------------------------------------------------------------

/**
 * POST /api/targets
 * @param {Object} profileIn — соответствует ProfileIn schema
 * @returns {Promise<{bmr, tdee, targets}>}
 */
export async function apiTargets(profileIn) {
  return apiFetch('/api/targets', {
    method: 'POST',
    body: JSON.stringify(profileIn),
  });
}

// ---- Menu generate ---------------------------------------------------------

/**
 * POST /api/menu/generate
 * @param {Object} profileIn
 * @param {number} seed
 * @param {'smoke'|'web'|'full'} config
 * @returns {Promise<MenuOut>}
 */
export async function apiGenerateMenu(profileIn, seed = 9001, config = 'web') {
  return apiFetch('/api/menu/generate', {
    method: 'POST',
    body: JSON.stringify({ profile: profileIn, seed, config }),
  });
}

// ---- Menu swap -------------------------------------------------------------

/**
 * POST /api/menu/swap
 * @param {Object} profileIn
 * @param {string[]} foodIds
 * @param {string} slot      e.g. "lunch_0"
 * @param {string|null} newFoodId
 * @param {number} seed
 * @returns {Promise<SwapOut>}
 */
export async function apiSwapMenu(profileIn, foodIds, slot, newFoodId = null, seed = 9001) {
  return apiFetch('/api/menu/swap', {
    method: 'POST',
    body: JSON.stringify({
      profile: profileIn,
      food_ids: foodIds,
      slot,
      new_food_id: newFoodId,
      seed,
    }),
  });
}

// ---- Food search -----------------------------------------------------------

/**
 * GET /api/foods?q=...&limit=...
 * @param {string} q
 * @param {number} limit
 * @returns {Promise<FoodItem[]>}
 */
export async function apiSearchFoods(q = '', limit = 20) {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return apiFetch(`/api/foods?${params}`);
}
