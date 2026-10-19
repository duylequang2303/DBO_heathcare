/**
 * Chart.js nutrition visualization
 */

let nutritionChart = null;

function setupRadarChart() {
    const canvas = document.getElementById('nutritionChart');
    const ctx = canvas.getContext('2d');
    
    nutritionChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Năng lượng', 'Protein', 'Carbs', 'Chất béo', 'Chất xơ'],
            datasets: [{
                label: '% Đạt mục tiêu',
                data: [0, 0, 0, 0, 0],
                backgroundColor: 'rgba(102, 126, 234, 0.2)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
            }]
        },
        options: {
            scales: {
                r: {
                    beginAtZero: true,
                    max: 120,
                    ticks: {
                        stepSize: 20
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function updateRadarChart(totals, targets) {
    if (!nutritionChart) {
        setupRadarChart();
    }
    
    const data = [
        (totals.calories / targets.calories) * 100,
        (totals.protein_g / targets.protein_g) * 100,
        (totals.carbs_g / targets.carbs_g) * 100,
        (totals.fat_g / targets.fat_g) * 100,
        (totals.fiber_g / targets.fiber_g) * 100,
    ];
    
    nutritionChart.data.datasets[0].data = data;
    nutritionChart.update();
}
