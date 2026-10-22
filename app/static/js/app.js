/**
 * Main application logic
 */

let currentMenu = null;
let currentProfile = null;

// Meal type labels
const MEAL_LABELS = {
    'breakfast': 'Sáng',
    'lunch': 'Trưa',
    'dinner': 'Tối',
    'snack': 'Phụ'
};

function getFormProfile() {
    return {
        name: document.getElementById('name').value,
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        height_cm: parseFloat(document.getElementById('height').value),
        weight_kg: parseFloat(document.getElementById('weight').value),
        activity_level: document.getElementById('activity').value,
        goal: document.getElementById('goal').value,
        meal_counts: { breakfast: 2, lunch: 2, dinner: 2, snack: 1 },
        medical_conditions: [],
        allergies: [],
        dislikes: []
    };
}

function renderTargets(data) {
    const html = `
        <div class="menu-summary">
            <div class="summary-card">
                <div class="value">${data.bmr.toFixed(0)}</div>
                <div class="label">BMR (kcal/ngày)</div>
            </div>
            <div class="summary-card">
                <div class="value">${data.tdee.toFixed(0)}</div>
                <div class="label">TDEE (kcal/ngày)</div>
            </div>
            <div class="summary-card">
                <div class="value">${data.targets.calories.toFixed(0)}</div>
                <div class="label">Mục tiêu calo</div>
            </div>
            <div class="summary-card">
                <div class="value">${data.targets.protein_g.toFixed(0)}g</div>
                <div class="label">Protein</div>
            </div>
            <div class="summary-card">
                <div class="value">${data.targets.carbs_g.toFixed(0)}g</div>
                <div class="label">Carbs</div>
            </div>
            <div class="summary-card">
                <div class="value">${data.targets.fat_g.toFixed(0)}g</div>
                <div class="label">Chất béo</div>
            </div>
        </div>
    `;
    
    document.getElementById('targetsDisplay').innerHTML = html;
    document.getElementById('targetsSection').style.display = 'block';
}

function renderMenu(menu) {
    // Summary
    const summaryHTML = `
        <div class="summary-card">
            <div class="value">${menu.fitness.toFixed(1)}</div>
            <div class="label">Fitness Score</div>
        </div>
        <div class="summary-card">
            <div class="value">${menu.totals.calories.toFixed(0)}</div>
            <div class="label">Tổng calo</div>
        </div>
        <div class="summary-card">
            <div class="value">${menu.totals.protein_g.toFixed(1)}g</div>
            <div class="label">Protein</div>
        </div>
        <div class="summary-card">
            <div class="value">${menu.totals.carbs_g.toFixed(1)}g</div>
            <div class="label">Carbs</div>
        </div>
        <div class="summary-card">
            <div class="value">${menu.totals.fat_g.toFixed(1)}g</div>
            <div class="label">Chất béo</div>
        </div>
    `;
    document.getElementById('menuSummary').innerHTML = summaryHTML;
    
    // Table
    const tableBody = document.getElementById('menuTableBody');
    tableBody.innerHTML = '';
    
    menu.items.forEach((item, index) => {
        const row = document.createElement('tr');
        const mealType = item.slot.split('_')[0];
        const mealLabel = MEAL_LABELS[mealType] || mealType;
        
        row.innerHTML = `
            <td class="meal-label">${mealLabel}</td>
            <td>${item.name}</td>
            <td>${item.portion_g_rounded}g</td>
            <td>${item.macros.calories.toFixed(0)}</td>
            <td>${item.macros.protein_g.toFixed(1)}</td>
            <td>${item.macros.carbs_g.toFixed(1)}</td>
            <td>${item.macros.fat_g.toFixed(1)}</td>
            <td>
                <button class="btn btn-small btn-secondary" onclick="handleSwap('${item.slot}')">
                    Thay món
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
    
    // Progress bars
    renderProgress(menu.totals, menu.targets);
    
    // Chart
    updateRadarChart(menu.totals, menu.targets);
    
    // Violations
    renderViolations(menu.violations);
    
    document.getElementById('menuSection').style.display = 'block';
}

function renderProgress(totals, targets) {
    const metrics = [
        { label: 'Năng lượng', current: totals.calories, target: targets.calories, unit: 'kcal', tolerance: 0.10 },
        { label: 'Protein', current: totals.protein_g, target: targets.protein_g, unit: 'g', tolerance: 0.15 },
        { label: 'Carbs', current: totals.carbs_g, target: targets.carbs_g, unit: 'g', tolerance: 0.15 },
        { label: 'Chất béo', current: totals.fat_g, target: targets.fat_g, unit: 'g', tolerance: 0.20 },
        { label: 'Chất xơ', current: totals.fiber_g, target: targets.fiber_g, unit: 'g', tolerance: 0.30 },
    ];
    
    const html = metrics.map(m => {
        const percent = (m.current / m.target) * 100;
        const diff = Math.abs(m.current - m.target);
        const diffPercent = (diff / m.target) * 100;
        
        let barClass = 'good';
        if (diffPercent > m.tolerance * 100) {
            barClass = 'danger';
        } else if (diffPercent > m.tolerance * 50) {
            barClass = 'warning';
        }
        
        return `
            <div class="progress-item">
                <div class="progress-label">
                    <span>${m.label}</span>
                    <span>${m.current.toFixed(1)} / ${m.target.toFixed(1)} ${m.unit} (${percent.toFixed(1)}%)</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar ${barClass}" style="width: ${Math.min(percent, 100)}%">
                        ${percent.toFixed(0)}%
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('progressBars').innerHTML = html;
}

function renderViolations(violations) {
    const container = document.getElementById('violationsDisplay');
    
    if (!violations || violations.length === 0) {
        container.innerHTML = '<p style="color: green; font-weight: 600;">✓ Không có vi phạm ràng buộc</p>';
        return;
    }
    
    const html = violations.map(v => `
        <div class="violation-item">⚠️ ${v}</div>
    `).join('');
    
    container.innerHTML = html;
}

async function handleSwap(slot) {
    if (!currentMenu || !currentProfile) return;
    
    const confirmed = confirm(`Bạn có muốn thay món ở vị trí "${slot}"?`);
    if (!confirmed) return;
    
    try {
        document.getElementById('loadingIndicator').style.display = 'block';
        
        const food_ids = currentMenu.items.map(item => item.food_id);
        const portions_g = currentMenu.items.map(item => item.portion_g);
        const seed = parseInt(document.getElementById('seed').value);
        
        const newMenu = await API.swapMenuItem(currentProfile, food_ids, portions_g, slot, null, seed);
        
        currentMenu = newMenu;
        renderMenu(newMenu);
        
        alert('✓ Đã thay món thành công!');
    } catch (error) {
        alert(`Lỗi khi thay món: ${error.message}`);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
}

// Event Handlers
document.getElementById('calcTargetsBtn').addEventListener('click', async () => {
    try {
        const profile = getFormProfile();
        const data = await API.calculateTargets(profile);
        renderTargets(data);
    } catch (error) {
        alert(`Lỗi: ${error.message}`);
    }
});

document.getElementById('profileForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    try {
        document.getElementById('loadingIndicator').style.display = 'block';
        document.getElementById('menuSection').style.display = 'none';
        
        const profile = getFormProfile();
        const seed = parseInt(document.getElementById('seed').value);
        
        currentProfile = profile;
        currentMenu = await API.generateMenu(profile, seed, 'web');
        
        renderMenu(currentMenu);
    } catch (error) {
        alert(`Lỗi: ${error.message}`);
    } finally {
        document.getElementById('loadingIndicator').style.display = 'none';
    }
});

// Initialize
setupRadarChart();
