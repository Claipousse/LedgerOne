/**
 * detail_categorie.js - Page détail d'une catégorie
 * - Navigation mensuelle + périodes (1M/3M/1A)
 * - Cercle de progression budget (Chart.js)
 * - Menu engrenage (Modifier/Supprimer)
 * - Formulaire modification inline
 * - Liste transactions paginées groupées par date
 */

// ============================================
//              VARIABLES GLOBALES
// ============================================
let categoryId = null;
let category = null;
let transactions = [];
let allTransactions = [];
let budgetChart = null;

// Navigation
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let currentPeriod = 1;

// Pagination
let currentPage = 1;
let itemsPerPage = 20;

// Limites
const TODAY = new Date();
const MAX_YEAR = TODAY.getFullYear();
const MAX_MONTH = TODAY.getMonth() + 1;

// Éléments DOM
const monthDisplay = document.getElementById('month-display');
const btnPrevMonth = document.getElementById('btn-prev-month');
const btnNextMonth = document.getElementById('btn-next-month');
const settingsBtn = document.getElementById('settings-btn');
const settingsDropdown = document.getElementById('settings-dropdown');
const editFormContainer = document.getElementById('edit-form-container');
const editForm = document.getElementById('edit-form');
const paginationSelect = document.getElementById('pagination-select');
const transactionsList = document.getElementById('transactions-list');
const paginationDiv = document.getElementById('pagination');

// ============================================
//              INITIALISATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Récupérer l'ID depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    categoryId = parseInt(urlParams.get('id'));

    if (!categoryId) {
        alert('❌ ID de catégorie manquant');
        window.location.href = 'categories.html';
        return;
    }

    updateMonthDisplay();
    setupEventListeners();
    loadCategoryData();
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
            currentPage = 1;
            updateMonthDisplay();
            loadCategoryData();
        });
    });

    // Menu engrenage
    settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsDropdown.classList.toggle('show');
    });

    // Fermer dropdown si clic ailleurs
    document.addEventListener('click', (e) => {
        if (!settingsBtn.contains(e.target) && !settingsDropdown.contains(e.target)) {
            settingsDropdown.classList.remove('show');
        }
    });

    // Formulaire modification
    editForm.addEventListener('submit', handleEditSubmit);

    // Sync color input & text
    document.getElementById('edit-color').addEventListener('input', (e) => {
        document.getElementById('edit-color-text').value = e.target.value;
    });

    document.getElementById('edit-color-text').addEventListener('input', (e) => {
        const color = e.target.value;
        if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
            document.getElementById('edit-color').value = color;
        }
    });

    // Pagination
    paginationSelect.addEventListener('change', (e) => {
        itemsPerPage = parseInt(e.target.value);
        currentPage = 1;
        renderTransactions();
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
    currentPage = 1;
    updateMonthDisplay();
    loadCategoryData();
}

function goToNextMonth() {
    if (isFutureMonth(currentYear, currentMonth + 1)) return;

    currentMonth++;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    currentPage = 1;
    updateMonthDisplay();
    loadCategoryData();
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
        monthDisplay.textContent = `${monthNames[currentMonth - 1]} ${currentYear}`;
    } else {
        const startDate = getStartDate();
        const endDate = getEndDate();

        const startMonthName = monthNames[startDate.getMonth()];
        const startYear = startDate.getFullYear();

        const endMonthName = monthNames[endDate.getMonth()];
        const endYear = endDate.getFullYear();

        monthDisplay.textContent = `${startMonthName} ${startYear} - ${endMonthName} ${endYear}`;
    }

    btnNextMonth.disabled = isFutureMonth(currentYear, currentMonth + 1);
}

function getStartDate() {
    const date = new Date(currentYear, currentMonth - 1, 1);
    if (currentPeriod > 1) {
        date.setMonth(date.getMonth() - (currentPeriod - 1));
    }
    return date;
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
//              CHARGEMENT DONNÉES
// ============================================
async function loadCategoryData() {
    try {
        showLoading();

        // Charger catégorie
        category = await getCategoryById(categoryId);

        // Calculer montant total période
        const startDate = getStartDate();
        const endDate = getEndDate();
        const months = getMonthsInPeriod(startDate, endDate);

        let totalAmount = 0;

        for (let { year, month } of months) {
            const result = await getMonthlyTotal(year, month, categoryId);
            totalAmount += result.total;
        }

        // Calculer % par rapport au total global
        let globalTotal = 0;
        for (let { year, month } of months) {
            const result = await getMonthlyTotal(year, month);
            globalTotal += result.total;
        }

        const percentage = globalTotal > 0 ? (totalAmount / globalTotal) * 100 : 0;

        // Charger transactions de la période
        const fromDate = formatDate(startDate);
        const toDate = formatDate(new Date(currentYear, currentMonth, 0)); // Dernier jour du mois

        allTransactions = await getAllTransactions({
            from_date: fromDate,
            to_date: toDate,
            category_id: categoryId,
            limit: 10000
        });

        // Afficher les infos
        displayCategoryInfo(totalAmount, percentage);
        renderTransactions();

        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
        console.error('Erreur:', error);
    }
}

function displayCategoryInfo(totalAmount, percentage) {
    // Nom + couleur
    const color = category.color || '#505050';
    document.getElementById('category-dot').style.backgroundColor = color;
    document.getElementById('category-name').textContent = category.name;

    // Montant
    document.getElementById('category-total').textContent = formatCurrency(totalAmount);

    // Stats
    document.getElementById('category-stats').textContent = 
        `${allTransactions.length} transaction${allTransactions.length > 1 ? 's' : ''} - ${percentage.toFixed(1)}%`;

    // Budget circle
    if (category.monthly_budget && category.monthly_budget > 0) {
        displayBudgetCircle(totalAmount);
        
        // Alerte si budget dépassé (avec budget ajusté selon période)
        const adjustedBudget = category.monthly_budget * currentPeriod;
        if (totalAmount > adjustedBudget) {
            showBudgetAlert(totalAmount);
        } else {
            hideBudgetAlert();
        }
    } else {
        hideBudgetCircle();
        hideBudgetAlert();
    }
}

function showBudgetAlert(totalAmount) {
    const existing = document.getElementById('budget-alert');
    if (existing) existing.remove();

    const alert = document.createElement('div');
    alert.id = 'budget-alert';
    alert.className = 'budget-alert';
    
    // Adapter le budget selon la période
    const adjustedBudget = category.monthly_budget * currentPeriod;
    const overspend = totalAmount - adjustedBudget;
    
    alert.innerHTML = `
        <span class="alert-icon">⚠️</span>
        <div class="alert-content">
            <div class="alert-title">Budget dépassé</div>
            <div class="alert-text">Vous avez dépassé le budget de ${formatCurrency(overspend)}</div>
        </div>
    `;

    const container = document.querySelector('.category-info-section');
    container.insertBefore(alert, container.firstChild);
}

function hideBudgetAlert() {
    const alert = document.getElementById('budget-alert');
    if (alert) alert.remove();
}

function displayBudgetCircle(totalAmount) {
    const container = document.getElementById('budget-circle-container');
    container.classList.remove('hidden');
    
    const categoryColor = category.color || '#818cf8';
    
    // Adapter le budget selon la période
    const adjustedBudget = category.monthly_budget * currentPeriod;
    
    container.innerHTML = `
        <canvas id="budget-circle" width="180" height="180"></canvas>
        <div class="budget-circle-text">
            <div class="budget-amount" id="budget-amount">${formatCurrency(adjustedBudget)}</div>
            <div class="budget-percentage" id="budget-percentage" style="color: ${categoryColor};">-</div>
        </div>
    `;

    const percentage = (totalAmount / adjustedBudget) * 100;
    document.getElementById('budget-percentage').textContent = `${percentage.toFixed(0)}%`;

    const ctx = document.getElementById('budget-circle');

    if (budgetChart) {
        budgetChart.destroy();
    }

    const remaining = Math.max(100 - percentage, 0);
    
    // Utiliser la couleur de la catégorie si définie, sinon violet par défaut
    const fillColor = percentage > 100 ? '#ef4444' : categoryColor;

    budgetChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, remaining],
                backgroundColor: [
                    fillColor,
                    'rgba(99, 102, 241, 0.1)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

function hideBudgetCircle() {
    const container = document.getElementById('budget-circle-container');
    container.innerHTML = '<div class="no-budget-text">Budget<br>non défini</div>';
}

// ============================================
//              TRANSACTIONS
// ============================================
function renderTransactions() {
    transactionsList.innerHTML = '';

    if (allTransactions.length === 0) {
        transactionsList.innerHTML = '<p class="empty-state">Aucune transaction</p>';
        paginationDiv.innerHTML = '';
        return;
    }

    // Grouper par date
    const grouped = groupByDate(allTransactions);

    // Pagination
    const keys = Object.keys(grouped);
    const totalPages = Math.ceil(keys.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageKeys = keys.slice(startIndex, endIndex);

    // Afficher
    pageKeys.forEach(dateKey => {
        const dateHeader = document.createElement('div');
        dateHeader.className = 'transaction-date-header';
        dateHeader.textContent = formatDateHeader(dateKey);
        transactionsList.appendChild(dateHeader);

        grouped[dateKey].forEach(tx => {
            const item = document.createElement('div');
            item.className = 'transaction-item';
            item.innerHTML = `
                <div class="transaction-bar"></div>
                <div class="transaction-desc">${tx.description}</div>
                <div class="transaction-amount">${formatCurrency(tx.amount)}</div>
            `;
            transactionsList.appendChild(item);
        });
    });

    // Pagination controls
    renderPagination(totalPages);
}

function groupByDate(transactions) {
    const grouped = {};

    transactions
        .sort((a, b) => new Date(b.date) - new Date(a.date))
        .forEach(tx => {
            const dateKey = tx.date;
            if (!grouped[dateKey]) {
                grouped[dateKey] = [];
            }
            grouped[dateKey].push(tx);
        });

    return grouped;
}

function formatDateHeader(dateStr) {
    const date = new Date(dateStr);
    const day = date.getDate().toString().padStart(2, '0');
    const monthNames = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
    const month = monthNames[date.getMonth()];
    const year = date.getFullYear();

    return `${day} ${month} ${year}`;
}

function renderPagination(totalPages) {
    paginationDiv.innerHTML = '';

    if (totalPages <= 1) return;

    // Bouton précédent
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '←';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderTransactions();
        }
    });
    paginationDiv.appendChild(prevBtn);

    // Numéros de page
    const maxButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxButtons - 1);

    if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = 'pagination-btn' + (i === currentPage ? ' active' : '');
        pageBtn.textContent = i;
        pageBtn.addEventListener('click', () => {
            currentPage = i;
            renderTransactions();
        });
        paginationDiv.appendChild(pageBtn);
    }

    // Bouton suivant
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = '→';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderTransactions();
        }
    });
    paginationDiv.appendChild(nextBtn);
}

// ============================================
//              MODIFICATION
// ============================================
function showEditForm() {
    settingsDropdown.classList.remove('show');

    // Pré-remplir le formulaire
    document.getElementById('edit-name').value = category.name;
    document.getElementById('edit-color').value = category.color || '#505050';
    document.getElementById('edit-color-text').value = category.color || '#505050';
    document.getElementById('edit-budget').value = category.monthly_budget || '';

    editFormContainer.classList.remove('hidden');
}

function hideEditForm() {
    editFormContainer.classList.add('hidden');
}

async function handleEditSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('edit-name').value.trim();
    const color = document.getElementById('edit-color').value;
    const budgetStr = document.getElementById('edit-budget').value.trim();
    const budget = budgetStr ? parseFloat(budgetStr) : null;

    if (!name) {
        alert('❌ Le nom est obligatoire');
        return;
    }

    try {
        showLoading();

        const updatedCategory = await updateCategory(categoryId, {
            name,
            color,
            monthly_budget: budget
        });

        category = updatedCategory;

        hideEditForm();
        await loadCategoryData();

        showSuccess('Catégorie modifiée');
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
}

// ============================================
//              SUPPRESSION
// ============================================
function confirmDelete() {
    settingsDropdown.classList.remove('show');
    document.getElementById('delete-category-name').textContent = category.name;
    document.getElementById('delete-modal').classList.add('show');
}

function hideDeleteModal() {
    document.getElementById('delete-modal').classList.remove('show');
}

async function deleteCategoryAction() {
    try {
        showLoading();
        await deleteCategory(categoryId); // Fonction de api.js
        alert('Catégorie supprimée');
        window.location.href = 'categories.html';
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
}

// ============================================
//              UTILITAIRES
// ============================================
function goBack() {
    window.location.href = 'categories.html';
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2
    }).format(amount);
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    return `${year}-${month}-${day}`;
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
    alert(message);
}

function showSuccess(message) {
    alert(message);
}
