/**
 * API client - wrapper functions for backend calls
 */

const API_BASE = '/api';

async function fetchJSON(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return response.json();
}

const API = {
    async healthCheck() {
        return fetchJSON(`${API_BASE}/health`);
    },
    
    async getProfiles() {
        return fetchJSON(`${API_BASE}/profiles`);
    },
    
    async calculateTargets(profile) {
        return fetchJSON(`${API_BASE}/targets`, {
            method: 'POST',
            body: JSON.stringify(profile),
        });
    },
    
    async generateMenu(profile, seed = 9001, config = 'web') {
        return fetchJSON(`${API_BASE}/menu/generate`, {
            method: 'POST',
            body: JSON.stringify({ profile, seed, config }),
        });
    },
    
    async swapMenuItem(profile, food_ids, portions_g, slot, new_food_id = null, seed = 9001) {
        return fetchJSON(`${API_BASE}/menu/swap`, {
            method: 'POST',
            body: JSON.stringify({
                profile,
                food_ids,
                portions_g,
                slot,
                new_food_id,
                seed,
            }),
        });
    },
    
    async searchFoods(query = '', limit = 20) {
        const params = new URLSearchParams({ limit });
        if (query) params.append('q', query);
        return fetchJSON(`${API_BASE}/foods?${params}`);
    },
};
