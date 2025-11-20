/**
 * sidebar-loader.js - Charge la sidebar depuis includes/sidebar.html
 * Gère automatiquement la classe "active" selon la page actuelle
 */

(function() {
    'use strict';

    /**
     * Détermine la page actuelle depuis l'URL
     * Ex: "categories.html" → "categories"
     *     "/" ou "index.html" → "index"
     */
    function getCurrentPage() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        // Si pas de fichier ou index.html → page "index"
        if (!filename || filename === 'index.html') {
            return 'index';
        }
        
        // Sinon, retirer l'extension .html
        return filename.replace('.html', '');
    }

    /**
     * Charge la sidebar et l'injecte dans le DOM
     */
    async function loadSidebar() {
        try {
            // Charger le fichier sidebar.html
            const response = await fetch('includes/sidebar.html');
            
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            
            const sidebarHTML = await response.text();
            
            // Injecter au début du body
            document.body.insertAdjacentHTML('afterbegin', sidebarHTML);
            
            // Activer le lien correspondant à la page actuelle
            setActiveLink();
            
        } catch (error) {
            console.error('Erreur lors du chargement de la sidebar:', error);
            // Afficher un message d'erreur discret
            document.body.insertAdjacentHTML('afterbegin', 
                '<div style="background: #ef4444; color: white; padding: 1rem; text-align: center;">' +
                '⚠️ Erreur de chargement du menu de navigation' +
                '</div>'
            );
        }
    }

    /**
     * Active le lien correspondant à la page actuelle
     */
    function setActiveLink() {
        const currentPage = getCurrentPage();
        const links = document.querySelectorAll('.sidebar-link');
        
        links.forEach(link => {
            if (link.dataset.page === currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // Charger la sidebar dès que le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadSidebar);
    } else {
        // DOM déjà chargé (cas rare)
        loadSidebar();
    }
})();