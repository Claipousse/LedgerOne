/**
 * categories.js - Gestion de la page Categories
 */

// Variables globales
let allCategories = [];
let filteredCategories = [];
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let currentPeriod = 1;
let currentSort = 'amount-desc';
let searchQuery = '';
let editingCategoryId = null;

const TODAY = new Date();
const MAX_YEAR = TODAY.getFullYear();
const MAX_MONTH = TODAY.getMonth() + 1;

const tbody = document.getElementById('categories-tbody');
const monthDisplay = document.getElementById('month-display');
const btnPrevMonth = document.getElementById('btn-prev-month');
const btnNextMonth = document.getElementById('btn-next-month');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const counterText = document.getElementById('counter-text');
const categoryCounter = document.getElementById('category-counter');
const categoryFormContainer = document.getElementById('category-form-container');
const categoryForm = document.getElementById('category-form');
const formTitle = document.getElementById('form-title');

document.addEventListener('DOMContentLoaded', () => {
    updateMonthDisplay();
    setupEventListeners();
    loadCategories();
});

function setupEventListeners() {
    btnPrevMonth.addEventListener('click', goToPreviousMonth);
    btnNextMonth.addEventListener('click', goToNextMonth);

    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentPeriod = parseInt(e.target.dataset.period);
            updateMonthDisplay();
            loadCategories();
        });
    });

    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        filterAndRender();
    });

    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        filterAndRender();
    });

    categoryForm.addEventListener('submit', handleFormSubmit);

    document.getElementById('form-color').addEventListener('input', (e) => {
        document.getElementById('form-color-text').value = e.target.value;
    });

    document.getElementById('form-color-text').addEventListener('input', (e) => {
        const color = e.target.value;
        if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
            document.getElementById('form-color').value = color;
        }
    });
}

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
    const monthNames = ['Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin', 
                        'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'];
    
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

async function loadCategories() {
    try {
        showLoading();
        
        allCategories = await getAllCategories();
        
        await calculateAmounts();
        
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

    for (let category of allCategories) {
        let total = 0;

        const months = getMonthsInPeriod(startDate, endDate);
        
        for (let { year, month } of months) {
            const result = await getMonthlyTotal(year, month, category.id);
            total += result.total;
        }

        category.amount = total;
        totalGlobal += total;
    }

    allCategories.forEach(cat => {
        cat.percentage = totalGlobal > 0 ? (cat.amount / totalGlobal) * 100 : 0;
    });
}

function getStartDate() {
    const date = new Date(currentYear, currentMonth - 1, 1);
    
    if (currentPeriod === 1) {
        return date;
    } else {
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

function filterAndRender() {
    if (searchQuery) {
        filteredCategories = allCategories.filter(cat => 
            cat.name.toLowerCase().includes(searchQuery)
        );
    } else {
        filteredCategories = [...allCategories];
    }

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

function renderTable() {
    tbody.innerHTML = '';

    if (filteredCategories.length === 0) {
        const message = searchQuery 
            ? 'Aucune categorie trouvee' 
            : 'Aucune categorie';
        tbody.innerHTML = `<tr><td colspan="5" class="text-center empty-state">${message}</td></tr>`;
        return;
    }

    filteredCategories.forEach(category => {
        const row = document.createElement('tr');
        
        const color = category.color || '#818cf8';
        const amount = formatCurrency(category.amount || 0);
        const percentage = (category.percentage || 0).toFixed(1);
        
        // Gestion du budget avec dépassement
        let budgetHTML = '';
        let budgetClass = '';
        
        if (category.monthly_budget) {
            const budgetValue = category.monthly_budget;
            const currentAmount = category.amount || 0;
            const isOverBudget = currentAmount > budgetValue;
            
            budgetClass = isOverBudget ? 'over-budget' : 'set';
            const warningIcon = isOverBudget 
                ? '<span class="budget-warning" title="Attention : le budget est depasse">⚠️</span>' 
                : '';
            
            budgetHTML = `${formatCurrency(budgetValue)} ${warningIcon}`;
        } else {
            budgetHTML = 'Non defini';
        }

        row.innerHTML = `
            <td>
                <div class="category-cell">
                    <span class="category-dot" style="background-color: ${color}; box-shadow: 0 0 12px ${color};"></span>
                    <span>${category.name}</span>
                </div>
            </td>
            <td class="amount-cell">${amount}</td>
            <td class="percentage-cell">${percentage}%</td>
            <td class="budget-cell ${budgetClass}">${budgetHTML}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon detail" onclick="goToDetail(${category.id})" title="Details">
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

    categoryCounter.textContent = `${count} categorie${count > 1 ? 's' : ''} de sorties`;
    
    if (searchQuery) {
        counterText.textContent = `${filteredCount} / ${count} categories`;
    } else {
        counterText.textContent = `${count} categorie${count > 1 ? 's' : ''} de sorties`;
    }
}

function showAddForm() {
    editingCategoryId = null;
    formTitle.textContent = 'Nouvelle categorie';

    document.getElementById('form-name').value = '';
    document.getElementById('form-color').value = '#818cf8';
    document.getElementById('form-color-text').value = '#818cf8';
    document.getElementById('form-budget').value = '';

    categoryFormContainer.classList.remove('hidden');
    categoryFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideCategoryForm() {
    categoryFormContainer.classList.add('hidden');
    editingCategoryId = null;
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const name = document.getElementById('form-name').value.trim();
    const color = document.getElementById('form-color').value;
    const budgetStr = document.getElementById('form-budget').value.trim();
    const budget = budgetStr ? parseFloat(budgetStr) : null;

    if (!name) {
        alert('Le nom est obligatoire');
        return;
    }

    if (budget !== null && budget < 0) {
        alert('Le budget doit etre positif ou nul');
        return;
    }

    try {
        showLoading();

        const data = {
            name,
            color,
            monthly_budget: budget
        };

        if (editingCategoryId) {
            await updateCategory(editingCategoryId, data);
        } else {
            await createCategory(data);
        }

        hideCategoryForm();
        await loadCategories();
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
}

function goToDetail(categoryId) {
    window.location.href = `detail_categorie.html?id=${categoryId}`;
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
    alert(message);
}
