/**
 * budget.js - Gestion de la page Budget
 * - Modification budget global
 * - KPIs et progression
 * - Alertes du mois
 * - Graphiques d'analyse
 */

// Variables globales
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let averageChart = null;
let budgetVsRealChart = null;

const globalBudgetFormContainer = document.getElementById('global-budget-form-container');
const globalBudgetForm = document.getElementById('global-budget-form');
const globalBudgetInput = document.getElementById('global-budget-input');
const alertsSection = document.getElementById('alerts-section');

// ============================================
//              INITIALISATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadBudgetData();
});

function setupEventListeners() {
    globalBudgetForm.addEventListener('submit', handleGlobalBudgetSubmit);
}

// ============================================
//              CHARGEMENT DONNÉES
// ============================================
async function loadBudgetData() {
    try {
        showLoading();

        // Charger paramètres globaux
        const settings = await getSettings();
        
        // Charger résumé du mois actuel
        const currentSummary = await getMonthlySummary(currentYear, currentMonth);
        
        // Charger alertes
        const alerts = await getBudgetAlerts(currentYear, currentMonth);

        // Afficher budget global
        displayGlobalBudget(settings, currentSummary);

        // Afficher alertes
        displayAlerts(alerts);

        // Afficher graphiques
        await displayCharts(currentSummary);

        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Erreur lors du chargement: ${error.message}`);
        console.error('Erreur:', error);
    }
}

// ============================================
//              BUDGET GLOBAL
// ============================================
function displayGlobalBudget(settings, currentSummary) {
    const globalBudget = settings.global_monthly_budget;
    const spent = currentSummary.total;

    if (!globalBudget || globalBudget === 0) {
        document.getElementById('global-budget-value').textContent = 'Non défini';
        document.getElementById('global-spent-value').textContent = formatCurrency(spent);
        document.getElementById('global-remaining-value').textContent = '-';
        document.getElementById('global-progress-percentage').textContent = '-';
        document.getElementById('global-progress-fill').style.width = '0%';
        document.getElementById('budget-days-info').textContent = '-';
        return;
    }

    const remaining = globalBudget - spent;
    const percentage = (spent / globalBudget) * 100;

    // KPIs
    document.getElementById('global-budget-value').textContent = formatCurrency(globalBudget);
    document.getElementById('global-spent-value').textContent = formatCurrency(spent);
    document.getElementById('global-remaining-value').textContent = formatCurrency(remaining);

    // Barre de progression
    const progressFill = document.getElementById('global-progress-fill');
    const progressPercentage = document.getElementById('global-progress-percentage');
    
    progressPercentage.textContent = `${percentage.toFixed(0)}%`;
    progressFill.style.width = `${Math.min(percentage, 100)}%`;

    // Couleur selon progression
    if (percentage > 100) {
        progressFill.style.background = 'linear-gradient(90deg, #ef4444 0%, #dc2626 100%)';
        progressPercentage.style.color = '#ef4444';
    } else if (percentage > 80) {
        progressFill.style.background = 'linear-gradient(90deg, #f59e0b 0%, #d97706 100%)';
        progressPercentage.style.color = '#f59e0b';
    } else {
        progressFill.style.background = 'linear-gradient(90deg, #818cf8 0%, #c084fc 100%)';
        progressPercentage.style.color = '#818cf8';
    }

    // Infos jours
    const today = new Date();
    const currentDay = today.getDate();
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    document.getElementById('budget-days-info').textContent = `Jour ${currentDay}/${daysInMonth}`;
}

// ============================================
//              MODIFICATION BUDGET
// ============================================
function showEditGlobalBudget() {
    // Pré-remplir avec valeur actuelle
    getSettings().then(settings => {
        if (settings.global_monthly_budget) {
            globalBudgetInput.value = settings.global_monthly_budget;
        } else {
            globalBudgetInput.value = '';
        }
    });

    globalBudgetFormContainer.classList.remove('hidden');
    globalBudgetFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideEditGlobalBudget() {
    globalBudgetFormContainer.classList.add('hidden');
}

async function handleGlobalBudgetSubmit(e) {
    e.preventDefault();

    const budgetStr = globalBudgetInput.value.trim();
    const budget = budgetStr ? parseFloat(budgetStr) : null;

    if (budget !== null && budget < 0) {
        alert('❌ Le budget doit être positif ou nul');
        return;
    }

    try {
        showLoading();

        await updateSettings(budget);

        hideEditGlobalBudget();
        await loadBudgetData();

        showSuccess('✅ Budget global mis à jour');
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
}

// ============================================
//              ALERTES
// ============================================
function displayAlerts(alertsData) {
    if (!alertsData.alerts || alertsData.alerts.length === 0) {
        alertsSection.classList.add('hidden');
        return;
    }

    alertsSection.classList.remove('hidden');
    alertsSection.innerHTML = '';

    alertsData.alerts.forEach(alert => {
        const alertCard = document.createElement('div');
        alertCard.className = 'budget-alert';

        let title, text;

        if (alert.scope === 'global') {
            title = '⚠️ Budget global dépassé';
            text = `Vous avez dépensé ${formatCurrency(alert.actual)} sur un budget de ${formatCurrency(alert.budget)}. Dépassement: ${formatCurrency(alert.delta)}`;
        } else {
            title = `⚠️ Budget "${alert.category}" dépassé`;
            text = `Dépensé: ${formatCurrency(alert.actual)} / Budget: ${formatCurrency(alert.budget)}. Dépassement: ${formatCurrency(alert.delta)}`;
        }

        alertCard.innerHTML = `
            <span class="alert-icon">⚠️</span>
            <div class="alert-content">
                <div class="alert-title">${title}</div>
                <div class="alert-text">${text}</div>
            </div>
        `;

        alertsSection.appendChild(alertCard);
    });
}

// ============================================
//              GRAPHIQUES
// ============================================
async function displayCharts(currentSummary) {
    // Charger les 3 derniers mois
    const months = getLastThreeMonths();
    const summaries = await Promise.all(
        months.map(m => getMonthlySummary(m.year, m.month))
    );

    // Graphique moyenne
    displayAverageChart(months, summaries, currentSummary);

    // Graphique budget vs réel
    await displayBudgetVsRealChart(months, summaries);
}

function displayAverageChart(months, summaries, currentSummary) {
    const ctx = document.getElementById('average-chart');
    if (!ctx) return;

    const labels = [...months.map(m => m.label), 'Ce mois'];
    const data = [...summaries.map(s => s.total), currentSummary.total];

    // Calculer moyenne
    const average = summaries.reduce((sum, s) => sum + s.total, 0) / summaries.length;

    if (averageChart) {
        averageChart.destroy();
    }

    averageChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Dépenses',
                    data: data,
                    backgroundColor: data.map((val, index) => 
                        index === data.length - 1 ? 'rgba(129, 140, 248, 0.8)' : 'rgba(161, 161, 170, 0.5)'
                    ),
                    borderColor: data.map((val, index) => 
                        index === data.length - 1 ? 'rgba(129, 140, 248, 1)' : 'rgba(161, 161, 170, 0.8)'
                    ),
                    borderWidth: 2,
                    borderRadius: 8
                },
                {
                    label: 'Moyenne 3 mois',
                    data: Array(labels.length).fill(average),
                    type: 'line',
                    borderColor: '#f59e0b',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }
            ]
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
                    display: true,
                    labels: {
                        color: '#a1a1aa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
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

async function displayBudgetVsRealChart(months, summaries) {
    const ctx = document.getElementById('budget-vs-real-chart');
    if (!ctx) return;

    // Récupérer budget global (on suppose qu'il est constant)
    const settings = await getSettings();
    const budget = settings.global_monthly_budget || 0;

    const labels = months.map(m => m.label);
    const realData = summaries.map(s => s.total);
    const budgetData = Array(labels.length).fill(budget);

    if (budgetVsRealChart) {
        budgetVsRealChart.destroy();
    }

    budgetVsRealChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Budget',
                    data: budgetData,
                    borderColor: '#4ade80',
                    backgroundColor: 'rgba(74, 222, 128, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Dépenses réelles',
                    data: realData,
                    borderColor: '#818cf8',
                    backgroundColor: 'rgba(129, 140, 248, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }
            ]
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
                    display: true,
                    labels: {
                        color: '#a1a1aa'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y);
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

// ============================================
//              UTILITAIRES
// ============================================
function getLastThreeMonths() {
    const months = [];
    const now = new Date();

    for (let i = 3; i >= 1; i--) {
        const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
        months.push({
            year: date.getFullYear(),
            month: date.getMonth() + 1,
            label: date.toLocaleDateString('fr-FR', { month: 'short' })
        });
    }

    return months;
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2
    }).format(amount);
}

function showLoading() {
    const main = document.querySelector('.main-content');
    const loading = document.createElement('div');
    loading.id = 'loading-overlay';
    loading.className = 'loading';
    loading.innerHTML = '<div class="spinner"></div>';
    main.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) loading.remove();
}

function showError(message) {
    alert('❌ ' + message);
}

function showSuccess(message) {
    const main = document.querySelector('.main-content');
    const success = document.createElement('div');
    success.className = 'error-message';
    success.style.background = 'rgba(34, 197, 94, 0.15)';
    success.style.borderColor = 'rgba(34, 197, 94, 0.4)';
    success.style.color = '#4ade80';
    success.innerHTML = `<strong>✅ Succès</strong><br>${message}`;
    
    main.insertBefore(success, main.firstChild);
    
    setTimeout(() => success.remove(), 3000);
}
