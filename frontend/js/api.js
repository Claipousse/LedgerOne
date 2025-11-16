/**
 * api.js - Module de communication avec l'API Backend
 * Contient toutes les fonctions fetch pour interagir avec LedgerOne API
 * Base URL : http://127.0.0.1:8000/api
 */

// Configuration de base
const API_BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Fonction utilitaire pour gérer les erreurs HTTP
 */
async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Erreur HTTP ${response.status}`);
    }
    return response.json();
}

// ============================================
//              CATEGORIES
// ============================================

async function getAllCategories() {
    const response = await fetch(`${API_BASE_URL}/categories/`);
    return handleResponse(response);
}

async function getCategoryById(id) {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`);
    return handleResponse(response);
}

async function createCategory(categoryData) {
    const response = await fetch(`${API_BASE_URL}/categories/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(categoryData)
    });
    return handleResponse(response);
}

async function updateCategory(id, categoryData) {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(categoryData)
    });
    return handleResponse(response);
}

async function deleteCategory(id) {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Erreur lors de la suppression: ${response.status}`);
    }
}

// ============================================
//              TRANSACTIONS
// ============================================

async function getAllTransactions(params = {}) {
    const queryParams = new URLSearchParams();
    
    if (params.skip !== undefined) queryParams.append('skip', params.skip);
    if (params.limit !== undefined) queryParams.append('limit', params.limit);
    if (params.from_date) queryParams.append('from_date', params.from_date);
    if (params.to_date) queryParams.append('to_date', params.to_date);
    if (params.category_id) queryParams.append('category_id', params.category_id);
    if (params.search) queryParams.append('search', params.search);
    
    const url = `${API_BASE_URL}/transactions/?${queryParams.toString()}`;
    const response = await fetch(url);
    return handleResponse(response);
}

async function getTransactionById(id) {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`);
    return handleResponse(response);
}

async function createTransaction(transactionData) {
    const response = await fetch(`${API_BASE_URL}/transactions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transactionData)
    });
    return handleResponse(response);
}

async function updateTransaction(id, transactionData) {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transactionData)
    });
    return handleResponse(response);
}

async function deleteTransaction(id) {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        throw new Error(`Erreur lors de la suppression: ${response.status}`);
    }
}

// ============================================
//              SETTINGS
// ============================================

async function getSettings() {
    const response = await fetch(`${API_BASE_URL}/settings/`);
    return handleResponse(response);
}

async function updateSettings(globalBudget) {
    const response = await fetch(`${API_BASE_URL}/settings/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ global_monthly_budget: globalBudget })
    });
    return handleResponse(response);
}

// ============================================
//              INSIGHTS
// ============================================

async function getMonthlySummary(year, month) {
    const response = await fetch(`${API_BASE_URL}/insights/summary?year=${year}&month=${month}`);
    return handleResponse(response);
}

async function getMonthlyTotal(year, month, categoryId = null) {
    let url = `${API_BASE_URL}/insights/monthly-total?year=${year}&month=${month}`;
    if (categoryId) url += `&category_id=${categoryId}`;
    
    const response = await fetch(url);
    return handleResponse(response);
}

async function getCategoryBreakdown(year, month) {
    const response = await fetch(`${API_BASE_URL}/insights/category-breakdown?year=${year}&month=${month}`);
    return handleResponse(response);
}

// ============================================
//              ALERTS
// ============================================

async function getBudgetAlerts(year, month) {
    const response = await fetch(`${API_BASE_URL}/alerts/?year=${year}&month=${month}`);
    return handleResponse(response);
}

// ============================================
//              IMPORT CSV
// ============================================

async function importCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/import/csv`, {
        method: 'POST',
        body: formData
    });
    return handleResponse(response);
}
