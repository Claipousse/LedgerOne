/**
 * transactions.js - Gestion de la page Transactions
 * - Affichage TOUTES les transactions (pas de navigation mois)
 * - Recherche temps réel
 * - Multiselect catégories avec autocomplete
 * - Tri (date, montant, nom)
 * - Pagination
 * - CRUD : Ajout/Modification/Suppression
 */

// ============================================
//              VARIABLES GLOBALES
// ============================================
let allTransactions = [];
let filteredTransactions = [];
let allCategories = [];
let selectedCategoryIds = [];
let searchQuery = '';
let currentSort = 'date-desc';
let currentPage = 1;
let itemsPerPage = 20;
let editingTransactionId = null;

// Éléments DOM
const transactionsList = document.getElementById('transactions-list');
const paginationDiv = document.getElementById('pagination');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const paginationSelect = document.getElementById('pagination-select');
const transactionCounter = document.getElementById('transaction-counter');
const multiselectBtn = document.getElementById('multiselect-btn');
const multiselectDropdown = document.getElementById('multiselect-dropdown');
const multiselectSearch = document.getElementById('multiselect-search');
const multiselectOptions = document.getElementById('multiselect-options');
const multiselectLabel = document.getElementById('multiselect-label');
const selectedTags = document.getElementById('selected-tags');
const transactionFormContainer = document.getElementById('transaction-form-container');
const transactionForm = document.getElementById('transaction-form');
const formTitle = document.getElementById('form-title');

// ============================================
//              INITIALISATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadData();
});

function setupEventListeners() {
    // Recherche
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        currentPage = 1;
        filterAndRender();
    });

    // Tri
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        currentPage = 1;
        filterAndRender();
    });

    // Pagination
    paginationSelect.addEventListener('change', (e) => {
        itemsPerPage = parseInt(e.target.value);
        currentPage = 1;
        filterAndRender();
    });

    // Multiselect
    multiselectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        multiselectDropdown.classList.toggle('show');
    });

    // Recherche dans multiselect
    multiselectSearch.addEventListener('input', (e) => {
        filterCategoryOptions(e.target.value.toLowerCase());
    });

    // Fermer dropdown si clic ailleurs
    document.addEventListener('click', (e) => {
        if (!multiselectBtn.contains(e.target) && !multiselectDropdown.contains(e.target)) {
            multiselectDropdown.classList.remove('show');
        }
    });

    // Formulaire
    transactionForm.addEventListener('submit', handleFormSubmit);

    // Limite date max = aujourd'hui
    document.getElementById('form-date').max = getTodayISO();
}

// ============================================
//              CHARGEMENT DONNÉES
// ============================================
async function loadData() {
    try {
        showLoading();

        // Charger catégories
        allCategories = await getAllCategories();

        // Charger TOUTES les transactions
        allTransactions = await getAllTransactions({ limit: 10000 });

        // Initialiser multiselect
        renderCategoryOptions();

        // Afficher
        filterAndRender();

        hideLoading();
    } catch (error) {
        hideLoading();
        showError(`Erreur lors du chargement: ${error.message}`);
        console.error('Erreur:', error);
    }
}

// ============================================
//              MULTISELECT CATÉGORIES
// ============================================
function renderCategoryOptions() {
    multiselectOptions.innerHTML = '';

    allCategories.forEach(cat => {
        const option = document.createElement('label');
        option.className = 'multiselect-option';
        option.dataset.categoryId = cat.id;
        option.dataset.categoryName = cat.name.toLowerCase();

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = cat.id;
        checkbox.checked = selectedCategoryIds.includes(cat.id);
        checkbox.addEventListener('change', (e) => {
            handleCategoryToggle(cat.id, e.target.checked);
        });

        const color = cat.color || '#505050';
        const dot = document.createElement('span');
        dot.className = 'category-dot';
        dot.style.backgroundColor = color;

        const label = document.createElement('span');
        label.textContent = cat.name;

        option.appendChild(checkbox);
        option.appendChild(dot);
        option.appendChild(label);

        multiselectOptions.appendChild(option);
    });
}

function filterCategoryOptions(query) {
    const options = multiselectOptions.querySelectorAll('.multiselect-option');

    options.forEach(option => {
        const name = option.dataset.categoryName;
        if (name.includes(query)) {
            option.style.display = 'flex';
        } else {
            option.style.display = 'none';
        }
    });
}

function handleCategoryToggle(categoryId, isChecked) {
    if (isChecked) {
        if (!selectedCategoryIds.includes(categoryId)) {
            selectedCategoryIds.push(categoryId);
        }
    } else {
        selectedCategoryIds = selectedCategoryIds.filter(id => id !== categoryId);
    }

    updateMultiselectLabel();
    updateSelectedTags();
    currentPage = 1;
    filterAndRender();
}

function updateMultiselectLabel() {
    if (selectedCategoryIds.length === 0) {
        multiselectLabel.textContent = 'Catégories';
    } else if (selectedCategoryIds.length === 1) {
        const cat = allCategories.find(c => c.id === selectedCategoryIds[0]);
        multiselectLabel.textContent = cat ? cat.name : 'Catégories';
    } else {
        multiselectLabel.textContent = `${selectedCategoryIds.length} catégories`;
    }
}

function updateSelectedTags() {
    selectedTags.innerHTML = '';

    selectedCategoryIds.forEach(categoryId => {
        const cat = allCategories.find(c => c.id === categoryId);
        if (!cat) return;

        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.innerHTML = `
            <span>${cat.name}</span>
            <button class="tag-remove" onclick="removeTag(${categoryId})">×</button>
        `;

        selectedTags.appendChild(tag);
    });
}

function removeTag(categoryId) {
    selectedCategoryIds = selectedCategoryIds.filter(id => id !== categoryId);

    // Décocher dans le multiselect
    const checkbox = multiselectOptions.querySelector(`input[value="${categoryId}"]`);
    if (checkbox) checkbox.checked = false;

    updateMultiselectLabel();
    updateSelectedTags();
    currentPage = 1;
    filterAndRender();
}

// ============================================
//              FILTRAGE & TRI
// ============================================
function filterAndRender() {
    // Copie
    filteredTransactions = [...allTransactions];

    // Filtre recherche
    if (searchQuery) {
        filteredTransactions = filteredTransactions.filter(tx =>
            tx.description.toLowerCase().includes(searchQuery)
        );
    }

    // Filtre catégories
    if (selectedCategoryIds.length > 0) {
        filteredTransactions = filteredTransactions.filter(tx =>
            selectedCategoryIds.includes(tx.category_id)
        );
    }

    // Tri
    const [column, direction] = currentSort.split('-');

    filteredTransactions.sort((a, b) => {
        let valA, valB;

        switch (column) {
            case 'date':
                valA = new Date(a.date);
                valB = new Date(b.date);
                break;
            case 'amount':
                valA = a.amount;
                valB = b.amount;
                break;
            case 'name':
                valA = a.description.toLowerCase();
                valB = b.description.toLowerCase();
                break;
            default:
                return 0;
        }

        if (valA < valB) return direction === 'asc' ? -1 : 1;
        if (valA > valB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    renderTransactions();
    updateCounter();
}

// ============================================
//              AFFICHAGE TRANSACTIONS
// ============================================
function renderTransactions() {
    transactionsList.innerHTML = '';

    if (filteredTransactions.length === 0) {
        const message = searchQuery || selectedCategoryIds.length > 0
            ? 'Aucune transaction trouvée'
            : 'Aucune transaction';
        transactionsList.innerHTML = `<p class="empty-state">${message}</p>`;
        paginationDiv.innerHTML = '';
        return;
    }

    // Pagination sur les transactions individuelles
    const totalPages = Math.ceil(filteredTransactions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedTransactions = filteredTransactions.slice(startIndex, endIndex);

    // Grouper par date (uniquement les transactions paginées)
    const grouped = groupByDate(paginatedTransactions);
    const keys = Object.keys(grouped);

    // Afficher
    keys.forEach(dateKey => {
        const dateHeader = document.createElement('div');
        dateHeader.className = 'transaction-date-header';
        dateHeader.textContent = formatDateHeader(dateKey);
        transactionsList.appendChild(dateHeader);

        grouped[dateKey].forEach(tx => {
            const item = document.createElement('div');
            item.className = 'transaction-item';

            // Catégorie
            let categoryHTML = '';
            if (tx.category) {
                const color = tx.category.color || '#505050';
                categoryHTML = `
                    <span class="category-dot" style="background-color: ${color}; box-shadow: 0 0 12px ${color};"></span>
                    <span class="transaction-category">${tx.category.name}</span>
                `;
            }

            item.innerHTML = `
                <div class="transaction-bar"></div>
                <div class="transaction-desc">${tx.description}</div>
                <div class="transaction-category-cell">${categoryHTML}</div>
                <div class="transaction-amount">${formatCurrency(tx.amount)}</div>
                <button class="transaction-menu-btn" onclick="showTransactionMenu(event, ${tx.id})">⋮</button>
            `;

            transactionsList.appendChild(item);
        });
    });

    // Pagination controls
    renderPagination(totalPages);
}

function groupByDate(transactions) {
    const grouped = {};

    transactions.forEach(tx => {
        const dateKey = tx.date;
        if (!grouped[dateKey]) {
            grouped[dateKey] = [];
        }
        grouped[dateKey].push(tx);
    });

    return grouped;
}

function formatDateHeader(dateStr) {
    const date = new Date(dateStr + 'T00:00:00');
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

function updateCounter() {
    const displayed = filteredTransactions.length;
    const total = allTransactions.length;
    transactionCounter.textContent = `${displayed} affichée${displayed > 1 ? 's' : ''} / ${total} total`;
}

// ============================================
//              MENU TRANSACTION
// ============================================
function showTransactionMenu(event, transactionId) {
    event.stopPropagation();

    // Supprimer menu existant
    const existingMenu = document.querySelector('.transaction-context-menu');
    if (existingMenu) existingMenu.remove();

    // Créer menu
    const menu = document.createElement('div');
    menu.className = 'transaction-context-menu';
    menu.innerHTML = `
        <button class="context-menu-item" onclick="editTransaction(${transactionId})">Modifier</button>
        <button class="context-menu-item delete" onclick="confirmDeleteTransaction(${transactionId})">Supprimer</button>
    `;

    // Positionner
    const rect = event.target.getBoundingClientRect();
    menu.style.top = rect.bottom + 'px';
    menu.style.left = (rect.left - 150) + 'px';

    document.body.appendChild(menu);

    // Fermer si clic ailleurs
    setTimeout(() => {
        document.addEventListener('click', function closeMenu() {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        });
    }, 10);
}

// ============================================
//              CRUD TRANSACTIONS
// ============================================
function showAddForm() {
    editingTransactionId = null;
    formTitle.textContent = 'Nouvelle transaction';

    // Réinitialiser
    document.getElementById('form-date').value = getTodayISO();
    document.getElementById('form-description').value = '';
    document.getElementById('form-amount').value = '';
    document.getElementById('form-category').value = '';

    // Remplir dropdown catégories
    populateCategorySelect();

    transactionFormContainer.classList.remove('hidden');
    transactionFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function editTransaction(transactionId) {
    try {
        const tx = await getTransactionById(transactionId);

        editingTransactionId = transactionId;
        formTitle.textContent = 'Modifier la transaction';

        document.getElementById('form-date').value = tx.date;
        document.getElementById('form-description').value = tx.description;
        document.getElementById('form-amount').value = tx.amount;
        document.getElementById('form-category').value = tx.category_id || '';

        populateCategorySelect();

        transactionFormContainer.classList.remove('hidden');
        transactionFormContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        showError(`Erreur : ${error.message}`);
    }
}

function populateCategorySelect() {
    const select = document.getElementById('form-category');
    select.innerHTML = '<option value="">Aucune</option>';

    allCategories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.name;
        select.appendChild(option);
    });
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const date = document.getElementById('form-date').value;
    const description = document.getElementById('form-description').value.trim();
    const amount = parseFloat(document.getElementById('form-amount').value);
    const categoryIdStr = document.getElementById('form-category').value;
    const categoryId = categoryIdStr ? parseInt(categoryIdStr) : null;

    // Validations
    if (!description) {
        alert('❌ La description est obligatoire');
        return;
    }

    if (amount === 0) {
        alert('❌ Le montant ne peut pas être 0');
        return;
    }

    if (new Date(date) > new Date()) {
        alert('❌ La date ne peut pas être dans le futur');
        return;
    }

    try {
        showLoading();

        const data = {
            date,
            description,
            amount,
            category_id: categoryId
        };

        if (editingTransactionId) {
            // Modification
            await updateTransaction(editingTransactionId, data);
        } else {
            // Création
            await createTransaction(data);
        }

        hideTransactionForm();
        await loadData();
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
}

function hideTransactionForm() {
    transactionFormContainer.classList.add('hidden');
    editingTransactionId = null;
}

function confirmDeleteTransaction(transactionId) {
    const tx = allTransactions.find(t => t.id === transactionId);
    if (!tx) return;

    document.getElementById('delete-transaction-desc').textContent = tx.description;
    document.getElementById('delete-modal').classList.add('show');

    // Stocker l'ID pour suppression
    window.deletingTransactionId = transactionId;
}

function hideDeleteModal() {
    document.getElementById('delete-modal').classList.remove('show');
    window.deletingTransactionId = null;
}

async function deleteTransactionAction() {
    const transactionId = window.deletingTransactionId;
    if (!transactionId) return;

    try {
        showLoading();
        await deleteTransaction(transactionId);
        hideDeleteModal();
        await loadData();
    } catch (error) {
        hideLoading();
        showError(`Erreur : ${error.message}`);
    }
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

function getTodayISO() {
    const today = new Date();
    const year = today.getFullYear();
    const month = (today.getMonth() + 1).toString().padStart(2, '0');
    const day = today.getDate().toString().padStart(2, '0');
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
    alert('❌ ' + message);
}

function showSuccess(message) {
    alert('✅ ' + message);
}
