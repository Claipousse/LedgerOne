/**
 * categories.js - Gestion de la page Catégories
 * - Navigation mensuelle avec blocage du futur
 * - Recherche en temps réel
 * - Tri via dropdown
 * - Calcul montants selon période (1M/3M/1A)
 * - Modification/Suppression (création sur page séparée)
 */

// ============================================
//              VARIABLES GLOBALES
// ============================================
let allCategories = [];
let filteredCategories = [];
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1; // 1-12
let currentPeriod = 1; // Par défaut 1 mois
let currentSort = 'amount-desc';
let searchQuery = '';

// Limites
const TODAY = new Date();
const MAX_YEAR = TODAY.getFullYear();
const MAX_MONTH = TODAY.getMonth() + 1;

// Éléments DOM
const tbody = document.getElementById('categories-tbody');
const monthDisplay = document.getElementById('month-display');
const btnPrevMonth = document.getElementById('btn-prev-month');
const btnNextMonth = document.getElementById('btn-next-month');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const counterText = document.getElementById('counter-text');
const categoryCounter = document.getElementById('category-counter');

// ============================================
//              INITIALISATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    updateMonthDisplay(); // Initialiser l'affichage dès le chargement
    setupEventListeners();
    loadCategories();
});

function setupEventListeners() {
    // Navigation mois
    btnPrevMonth.addEventListener('click', goToPreviousMonth);
    btnNextMonth.addEventListener('click', goToNextMonth);

    // Boutons période
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentPeriod = parseInt(e.target.dataset.period);
            updateMonthDisplay(); // Mettre à jour l'affichage de la période
            loadCategories();
        });
    });

    // Recherche temps réel
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        filterAndRender();
    });

    // Tri
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        filterAndRender();
    });
}

// ============================================
//              NAVIGATION MOIS
// ============================================
function goToPreviousMonth() {
    currentMonth--;
    if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    updateMonthDisplay();
    loadCategories();
}

function goToNextMonth() {
    // Bloquer si on essaie d'aller dans le futur
    if (isFutureMonth(currentYear, currentMonth + 1)) {
        return;
    }

    currentMonth++;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    updateMonthDisplay();
    loadCategories();
}

function isFutureMonth(year, month) {
    if (year > MAX_YEAR) return true;
    if (year === MAX_YEAR && month > MAX_MONTH) return true;
    return false;
}

function updateMonthDisplay() {
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    
    if (currentPeriod === 1) {
        // 1M : "Novembre 2025"
        monthDisplay.textContent = `${monthNames[currentMonth - 1]} ${currentYear}`;
    } else {
        // 3M ou 1A : afficher la plage "Début - Fin"
        const startDate = getStartDate();
        const endDate = getEndDate();
        
        const startMonthName = monthNames[startDate.getMonth()];
        const startYear = startDate.getFullYear();
        
        const endMonthName = monthNames[endDate.getMonth()];
        const endYear = endDate.getFullYear();
        
        monthDisplay.textContent = `${startMonthName} ${startYear} - ${endMonthName} ${endYear}`;
    }

    // Désactiver flèche droite si mois futur
    btnNextMonth.disabled = isFutureMonth(currentYear, currentMonth + 1);
}

// ============================================
//              CHARGEMENT DONNÉES
// ============================================
async function loadCategories() {
    try {
        showLoading();
        
        // Charger toutes les catégories
        allCategories = await getAllCategories();
        
        // Calculer les montants selon la période
        await calculateAmounts();
        
        // Filtrer et afficher
        filterAndRender();
        
        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Erreur lors du chargement: ${error.message}`);
        console.error('Erreur:', error);
    }
}

async function calculateAmounts() {
    const startDate = getStartDate();
    const endDate = getEndDate();
    
    let totalGlobal = 0;

    // Pour chaque catégorie, récupérer le total sur la période
    for (let category of allCategories) {
        let total = 0;

        // Parcourir tous les mois de la période
        const months = getMonthsInPeriod(startDate, endDate);
        
        for (let { year, month } of months) {
            const result = await getMonthlyTotal(year, month, category.id);
            total += result.total;
        }

        category.amount = total;
        totalGlobal += total;
    }

    // Calculer les pourcentages
    allCategories.forEach(cat => {
        cat.percentage = totalGlobal > 0 ? (cat.amount / totalGlobal) * 100 : 0;
    });
}

function getStartDate() {
    const date = new Date(currentYear, currentMonth - 1, 1);
    
    if (currentPeriod === 1) {
        // 1M : juste le mois actuel
        return date;
    } else {
        // 3M ou 1A : remonter de X mois
        date.setMonth(date.getMonth() - (currentPeriod - 1));
        return date;
    }
}

function getEndDate() {
    return new Date(currentYear, currentMonth - 1, 1);
}

function getMonthsInPeriod(startDate, endDate) {
    const months = [];
    const current = new Date(startDate);
    
    while (current <= endDate) {
        months.push({
            year: current.getFullYear(),
            month: current.getMonth() + 1
        });
        current.setMonth(current.getMonth() + 1);
    }
    
    return months;
}

// ============================================
//              FILTRAGE & TRI
// ============================================
function filterAndRender() {
    // Filtrer par recherche
    if (searchQuery) {
        filteredCategories = allCategories.filter(cat => 
            cat.name.toLowerCase().includes(searchQuery)
        );
    } else {
        filteredCategories = [...allCategories];
    }

    // Trier
    const [column, direction] = currentSort.split('-');
    
    filteredCategories.sort((a, b) => {
        let valA, valB;

        switch (column) {
            case 'name':
                valA = a.name.toLowerCase();
                valB = b.name.toLowerCase();
                break;
            case 'amount':
                valA = a.amount || 0;
                valB = b.amount || 0;
                break;
            case 'percentage':
                valA = a.percentage || 0;
                valB = b.percentage || 0;
                break;
            case 'budget':
                valA = a.monthly_budget || 0;
                valB = b.monthly_budget || 0;
                break;
            default:
                return 0;
        }

        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    renderTable();
    updateCounters();
}

// ============================================
//              AFFICHAGE TABLEAU
// ============================================
function renderTable() {
    tbody.innerHTML = '';

    if (filteredCategories.length === 0) {
        const message = searchQuery 
            ? 'Aucune catégorie trouvée' 
            : 'Aucune catégorie';
        tbody.innerHTML = `<tr><td colspan="5" class="text-center empty-state">${message}</td></tr>`;
        return;
    }

    filteredCategories.forEach(category => {
        const row = document.createElement('tr');
        
        const color = category.color || '#505050';
        const amount = formatCurrency(category.amount || 0);
        const percentage = (category.percentage || 0).toFixed(1);
        const budget = category.monthly_budget 
            ? formatCurrency(category.monthly_budget) 
            : 'Non défini';
        const budgetClass = category.monthly_budget ? 'set' : '';

        row.innerHTML = `
            <td>
                <div class="category-cell">
                    <span class="category-dot" style="background-color: ${color}"></span>
                    <span>${category.name}</span>
                </div>
            </td>
            <td class="amount-cell">${amount}</td>
            <td class="percentage-cell">${percentage}%</td>
            <td class="budget-cell ${budgetClass}">${budget}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon detail" onclick="goToDetail(${category.id})" title="Détails">
                        →
                    </button>
                </div>
            </td>
        `;

        tbody.appendChild(row);
    });
}

function updateCounters() {
    const count = allCategories.length;
    const filteredCount = filteredCategories.length;

    categoryCounter.textContent = `${count} catégorie${count > 1 ? 's' : ''} de sorties`;
    
    if (searchQuery) {
        counterText.textContent = `${filteredCount} / ${count} catégories`;
    } else {
        counterText.textContent = `${count} catégorie${count > 1 ? 's' : ''} de sorties`;
    }
}

// ============================================
//              ACTIONS
// ============================================
function goToDetail(categoryId) {
    window.location.href = `detail_categorie.html?id=${categoryId}`;
}

// ============================================
//              UTILITAIRES
// ============================================
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
    alert('✅ ' + message);
}
