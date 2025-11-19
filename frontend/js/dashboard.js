/**
 * dashboard.js - Logique du Dashboard LedgerOne
 * - Comparaison avec mois dernier pour KPI
 * - Bar chart 3 derniers mois
 * - Camembert avec couleurs catégories
 * - Tableau Top 5
 */

// Variables globales
let pieChart = null;
let barChart = null;
let currentPiePeriod = 1;

// Palette de couleurs par défaut si catégorie n'a pas de couleur
const DEFAULT_COLORS = [
    '#8b7ff5', // Violet (Loisir)
    '#a78bfa', // Violet clair (Alimentation) 
    '#fbbf24', // Jaune/Orange (Charges)
    '#34d399', // Vert (Education)
    '#ef4444', // Rouge (Animaux)
    '#3b82f6', // Bleu
    '#ec4899', // Rose
    '#14b8a6', // Teal
    '#f97316', // Orange
    '#a855f7'  // Violet
];

/**
 * Formater un montant en euros
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2
    }).format(amount);
}

/**
 * Obtenir le mois actuel et le mois dernier
 */
function getCurrentAndPreviousMonth() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    
    // Calculer le mois précédent
    let previousYear = currentYear;
    let previousMonth = currentMonth - 1;
    
    if (previousMonth === 0) {
        previousMonth = 12;
        previousYear -= 1;
    }
    
    return {
        current: { year: currentYear, month: currentMonth },
        previous: { year: previousYear, month: previousMonth }
    };
}

/**
 * Obtenir les 3 derniers mois (pour bar chart)
 */
function getLastThreeMonths() {
    const months = [];
    const now = new Date();
    
    for (let i = 2; i >= 0; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        months.push({
            year: date.getFullYear(),
            month: date.getMonth() + 1,
            label: date.toLocaleDateString('fr-FR', { month: 'short' })
        });
    }
    
    return months;
}

/**
 * Calculer le pourcentage de variation entre deux valeurs
 */
function calculatePercentageChange(current, previous) {
    if (previous === 0) {
        return current > 0 ? 100 : 0;
    }
    return ((current - previous) / previous) * 100;
}

/**
 * Initialiser le dashboard
 */
async function initDashboard() {
    try {
        showLoading();
        
        const { current, previous } = getCurrentAndPreviousMonth();
        
        // Charger les données du mois actuel et du mois précédent
        const [currentSummary, previousSummary, settings] = await Promise.all([
            getMonthlySummary(current.year, current.month),
            getMonthlySummary(previous.year, previous.month),
            getSettings()
        ]);
        
        hideLoading();
        
        // Afficher les KPI avec comparaisons
        displayKPIs(currentSummary, previousSummary, settings);
        
        // Afficher les graphiques
        await displayCharts(currentSummary);
        
        // Afficher le tableau Top 5
        displayTop5Table(currentSummary);

        // Event listeners pour les boutons de période du camembert
        document.querySelectorAll('.chart-card .period-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                document.querySelectorAll('.chart-card .period-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                currentPiePeriod = parseInt(e.target.dataset.period);
                await updatePieChart();
            });
        });
        
    } catch (error) {
        hideLoading();
        showError(`Erreur lors du chargement du dashboard: ${error.message}`);
        console.error('Erreur dashboard:', error);
    }
}

function displayKPIs(current, previous, settings) {
    // KPI 1: Total des dépenses
    document.getElementById('kpi-total').textContent = formatCurrency(current.total);
    
    // KPI 2: Nombre d'opérations
    document.getElementById('kpi-count').textContent = current.count;
    
    // KPI 3: Budget restant
    if (settings.global_monthly_budget && settings.global_monthly_budget > 0) {
        const remaining = settings.global_monthly_budget - current.total;
        
        if (remaining < 0) {
            document.getElementById('kpi-budget').textContent = 'Dépassé';
        } else {
            document.getElementById('kpi-budget').textContent = formatCurrency(remaining);
        }
    } else {
        document.getElementById('kpi-budget').textContent = 'Non défini';
    }
    
    // KPI 4: Opérations moyennes par jour
    const daysInMonth = new Date(
        getCurrentAndPreviousMonth().current.year,
        getCurrentAndPreviousMonth().current.month,
        0
    ).getDate();
    const avgPerDay = current.count > 0 ? (current.count / daysInMonth).toFixed(1) : 0;
    document.getElementById('kpi-avg').textContent = avgPerDay;
}

/**
 * Mettre à jour l'indicateur de tendance
 */
function updateTrendIndicator(elementId, value, isAbsolute = false) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    let displayValue;
    let arrow;
    
    if (isAbsolute) {
        // Nombre absolu (ex: +8 opérations)
        displayValue = value > 0 ? `+${value}` : value.toString();
        arrow = value > 0 ? '↗' : (value < 0 ? '↘' : '→');
    } else {
        // Pourcentage
        displayValue = value > 0 ? `+${value.toFixed(1)}%` : `${value.toFixed(1)}%`;
        arrow = value > 0 ? '↗' : (value < 0 ? '↘' : '→');
    }
    
    // Appliquer la classe CSS
    element.classList.remove('positive', 'negative');
    if (value > 0) {
        element.classList.add('positive');
    } else if (value < 0) {
        element.classList.add('negative');
    }
    
    element.innerHTML = `<span class="trend-arrow">${arrow}</span> ${displayValue}`;
}

/**
 * Afficher les graphiques
 */
async function displayCharts(currentSummary) {
    if (Object.keys(currentSummary.by_category).length === 0) {
        document.getElementById('pie-chart').parentElement.innerHTML = 
            '<p class="empty-state">Aucune donnée à afficher</p>';
        document.getElementById('bar-chart').parentElement.innerHTML = 
            '<p class="empty-state">Aucune donnée à afficher</p>';
        return;
    }
    
    // Récupérer les catégories avec leurs couleurs
    const categories = await getAllCategories();
    const categoryColors = {};
    categories.forEach((cat, index) => {
        // Utiliser la couleur de la catégorie si définie, sinon palette par défaut
        categoryColors[cat.name] = cat.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
    });
    
    // Pie Chart
    displayPieChart(currentSummary.by_category, categoryColors);
    
    // Bar Chart (3 derniers mois)
    await displayBarChart();
}

/**
 * Afficher le Pie Chart
 */
function displayPieChart(byCategory, categoryColors) {
    const ctx = document.getElementById('pie-chart');
    if (!ctx) return;
    
    const labels = Object.keys(byCategory);
    const data = labels.map(cat => byCategory[cat].total);
    const colors = labels.map(cat => categoryColors[cat] || '#cccccc');
    
    // Détruire le graphique existant
    if (pieChart) {
        pieChart.destroy();
    }
    
    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: '#1a1a2e',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false // On utilise une légende custom
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatCurrency(context.parsed);
                            const percentage = byCategory[label].percentage.toFixed(0);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Afficher le Bar Chart (3 derniers mois)
 */
async function displayBarChart() {
    const ctx = document.getElementById('bar-chart');
    if (!ctx) return;
    
    const months = getLastThreeMonths();
    
    // Charger les totaux des 3 derniers mois
    const totals = await Promise.all(
        months.map(m => getMonthlyTotal(m.year, m.month))
    );
    
    const labels = months.map(m => m.label);
    const data = totals.map(t => t.total);
    
    // Détruire le graphique existant
    if (barChart) {
        barChart.destroy();
    }
    
    barChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Dépenses',
                data: data,
                backgroundColor: 'rgba(129, 140, 248, 0.8)', // Violet moderne et visible
                borderColor: 'rgba(129, 140, 248, 1)',
                borderWidth: 2,
                borderRadius: 8,
                barThickness: 60
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        },
                        color: '#a1a1aa'
                    },
                    grid: {
                        color: 'rgba(99, 102, 241, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#a1a1aa'
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y);
                        }
                    },
                    backgroundColor: 'rgba(26, 26, 46, 0.9)',
                    borderColor: 'rgba(99, 102, 241, 0.5)',
                    borderWidth: 1
                }
            }
        }
    });
}

/**
 * Afficher le tableau Top 5
 */
function displayTop5Table(summary) {
    const tbody = document.getElementById('top5-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    // Trier les catégories par montant décroissant
    const sorted = Object.entries(summary.by_category)
        .sort((a, b) => b[1].total - a[1].total)
        .slice(0, 5); // Top 5
    
    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Aucune donnée</td></tr>';
        return;
    }
    
    // Récupérer les catégories pour les couleurs
    getAllCategories().then(categories => {
        const categoryColors = {};
        categories.forEach((cat, index) => {
            categoryColors[cat.name] = cat.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
        });
        
        sorted.forEach(([categoryName, data], index) => {
            const row = document.createElement('tr');
            const color = categoryColors[categoryName] || '#cccccc';
            
            row.innerHTML = `
                <td class="rank-cell">${index + 1}</td>
                <td>
                    <div class="category-cell">
                        <span class="category-dot" style="background-color: ${color}; box-shadow: 0 0 12px ${color};"></span>
                        <span>${categoryName}</span>
                    </div>
                </td>
                <td class="percentage-cell">${data.percentage.toFixed(0)}%</td>
                <td class="amount-cell">${formatCurrency(data.total)}</td>
            `;
            
            tbody.appendChild(row);
        });
    });
}

/**
 * Afficher l'état de chargement
 */
function showLoading() {
    const main = document.querySelector('.main-content');
    if (!main) return;
    
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.className = 'loading';
    loading.innerHTML = '<div class="spinner"></div>';
    
    main.appendChild(loading);
}

/**
 * Masquer l'état de chargement
 */
function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

/**
 * Afficher un message d'erreur
 */
function showError(message) {
    const main = document.querySelector('.main-content');
    if (!main) return;
    
    const error = document.createElement('div');
    error.className = 'error-message';
    error.innerHTML = `<strong>⚠ Erreur</strong><br>${message}`;
    
    main.insertBefore(error, main.firstChild);
    
    setTimeout(() => error.remove(), 10000);
}

/**
 * Mettre à jour le camembert selon la période sélectionnée
 */
async function updatePieChart() {
    try {
        showLoading();
        
        const now = new Date();
        const currentYear = now.getFullYear();
        const currentMonth = now.getMonth() + 1;
        
        let totalByCategory = {};
        let subtitle = '';
        
        if (currentPiePeriod === 1) {
            // 1 mois (mois actuel)
            const summary = await getMonthlySummary(currentYear, currentMonth);
            totalByCategory = summary.by_category;
            subtitle = 'Distribution des dépenses ce mois';
            
        } else if (currentPiePeriod === 3) {
            // 3 derniers mois
            subtitle = 'Distribution des dépenses sur 3 mois';
            
            for (let i = 0; i < 3; i++) {
                let month = currentMonth - i;
                let year = currentYear;
                
                if (month <= 0) {
                    month += 12;
                    year -= 1;
                }
                
                const summary = await getMonthlySummary(year, month);
                
                // Additionner les totaux par catégorie
                Object.entries(summary.by_category).forEach(([catName, data]) => {
                    if (!totalByCategory[catName]) {
                        totalByCategory[catName] = { total: 0, count: 0 };
                    }
                    totalByCategory[catName].total += data.total;
                    totalByCategory[catName].count += data.count;
                });
            }
            
            // Recalculer les pourcentages
            const grandTotal = Object.values(totalByCategory).reduce((sum, cat) => sum + cat.total, 0);
            Object.keys(totalByCategory).forEach(catName => {
                totalByCategory[catName].percentage = (totalByCategory[catName].total / grandTotal) * 100;
            });
            
        } else if (currentPiePeriod === 12) {
            // Année en cours (janvier à mois actuel)
            subtitle = `Distribution des dépenses en ${currentYear}`;
            
            for (let month = 1; month <= currentMonth; month++) {
                const summary = await getMonthlySummary(currentYear, month);
                
                // Additionner les totaux par catégorie
                Object.entries(summary.by_category).forEach(([catName, data]) => {
                    if (!totalByCategory[catName]) {
                        totalByCategory[catName] = { total: 0, count: 0 };
                    }
                    totalByCategory[catName].total += data.total;
                    totalByCategory[catName].count += data.count;
                });
            }
            
            // Recalculer les pourcentages
            const grandTotal = Object.values(totalByCategory).reduce((sum, cat) => sum + cat.total, 0);
            Object.keys(totalByCategory).forEach(catName => {
                totalByCategory[catName].percentage = (totalByCategory[catName].total / grandTotal) * 100;
            });
        }
        
        // Mettre à jour le sous-titre
        document.getElementById('pie-subtitle').textContent = subtitle;
        
        // Récupérer les couleurs des catégories
        const categories = await getAllCategories();
        const categoryColors = {};
        categories.forEach((cat, index) => {
            categoryColors[cat.name] = cat.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
        });
        
        // Mettre à jour le graphique
        displayPieChart(totalByCategory, categoryColors);
        
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showError(`Erreur lors de la mise à jour: ${error.message}`);
        console.error('Erreur:', error);
    }
}

// Initialiser au chargement de la page
document.addEventListener('DOMContentLoaded', initDashboard);
