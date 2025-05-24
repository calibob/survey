/**
 * Gestion de la pagination des sondages
 * 
 * Ce script permet de naviguer entre les différentes pages d'un sondage,
 * définies par les sauts de page (pagebreaks).
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser la pagination
    initPagination();
    
    // Configurer les boutons de navigation
    setupNavigationButtons();
    
    // Configurer la barre de progression
    setupProgressBar();
});

/**
 * Initialise la pagination en masquant toutes les pages sauf la première
 */
function initPagination() {
    // Récupérer toutes les pages du sondage
    const pages = document.querySelectorAll('.survey-page');
    
    if (pages.length <= 1) {
        // S'il n'y a qu'une seule page, pas besoin de pagination
        const paginationControls = document.querySelector('.pagination-controls');
        if (paginationControls) {
            paginationControls.style.display = 'none';
        }
        return;
    }
    
    // Masquer toutes les pages sauf la première
    pages.forEach((page, index) => {
        if (index === 0) {
            page.classList.add('active');
            page.style.display = 'block';
        } else {
            page.classList.remove('active');
            page.style.display = 'none';
        }
    });
    
    // Mettre à jour l'état des boutons de navigation
    updateNavigationState(0, pages.length);
}

/**
 * Configure les boutons de navigation (précédent, suivant, soumettre)
 */
function setupNavigationButtons() {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const submitButton = document.getElementById('submit-survey');
    
    // Récupérer toutes les pages du sondage
    const pages = document.querySelectorAll('.survey-page');
    
    if (prevButton) {
        prevButton.addEventListener('click', function() {
            navigateTo('prev');
        });
    }
    
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            if (validateCurrentPage()) {
                navigateTo('next');
            }
        });
    }
    
    if (submitButton) {
        submitButton.addEventListener('click', function(event) {
            if (!validateAllPages()) {
                event.preventDefault();
                alert('Veuillez remplir tous les champs obligatoires avant de soumettre le sondage.');
            }
        });
    }
}

/**
 * Configure la barre de progression du sondage
 */
function setupProgressBar() {
    const progressBar = document.querySelector('.survey-progress-bar');
    if (!progressBar) return;
    
    const pages = document.querySelectorAll('.survey-page');
    
    // Créer les indicateurs de progression pour chaque page
    pages.forEach((page, index) => {
        const indicator = document.createElement('div');
        indicator.classList.add('progress-indicator');
        indicator.dataset.page = index;
        
        if (index === 0) {
            indicator.classList.add('active');
        }
        
        // Ajouter un tooltip avec le titre de la page si disponible
        const pageTitle = page.querySelector('.page-title');
        if (pageTitle) {
            indicator.title = pageTitle.textContent;
        } else {
            indicator.title = `Page ${index + 1}`;
        }
        
        // Permettre de naviguer directement vers une page en cliquant sur l'indicateur
        indicator.addEventListener('click', function() {
            const currentIndex = getCurrentPageIndex();
            
            // Ne pas permettre de sauter des pages sans les valider
            if (index > currentIndex) {
                for (let i = currentIndex; i < index; i++) {
                    if (!validatePage(i)) {
                        return;
                    }
                }
            }
            
            navigateToPage(index);
        });
        
        progressBar.appendChild(indicator);
    });
}

/**
 * Navigue vers la page précédente ou suivante
 * 
 * @param {string} direction - Direction ('prev' ou 'next')
 */
function navigateTo(direction) {
    const pages = document.querySelectorAll('.survey-page');
    const currentIndex = getCurrentPageIndex();
    
    let targetIndex;
    if (direction === 'prev') {
        targetIndex = Math.max(0, currentIndex - 1);
    } else {
        targetIndex = Math.min(pages.length - 1, currentIndex + 1);
    }
    
    navigateToPage(targetIndex);
}

/**
 * Navigue vers une page spécifique
 * 
 * @param {number} pageIndex - Index de la page cible
 */
function navigateToPage(pageIndex) {
    const pages = document.querySelectorAll('.survey-page');
    const currentIndex = getCurrentPageIndex();
    
    // Ne rien faire si c'est déjà la page active
    if (pageIndex === currentIndex) return;
    
    // Masquer la page actuelle
    pages[currentIndex].classList.remove('active');
    pages[currentIndex].style.display = 'none';
    
    // Afficher la nouvelle page avec une animation
    const targetPage = pages[pageIndex];
    targetPage.style.opacity = 0;
    targetPage.style.display = 'block';
    
    setTimeout(() => {
        targetPage.classList.add('active');
        targetPage.style.transition = 'opacity 0.3s ease';
        targetPage.style.opacity = 1;
        
        // Faire défiler vers le haut de la nouvelle page
        window.scrollTo({
            top: targetPage.offsetTop - 50,
            behavior: 'smooth'
        });
    }, 10);
    
    // Mettre à jour l'état des boutons de navigation
    updateNavigationState(pageIndex, pages.length);
    
    // Mettre à jour la barre de progression
    updateProgressBar(pageIndex);
}

/**
 * Récupère l'index de la page active
 * 
 * @returns {number} - Index de la page active
 */
function getCurrentPageIndex() {
    const activePage = document.querySelector('.survey-page.active');
    const pages = document.querySelectorAll('.survey-page');
    
    return Array.from(pages).indexOf(activePage);
}

/**
 * Met à jour l'état des boutons de navigation
 * 
 * @param {number} currentIndex - Index de la page active
 * @param {number} totalPages - Nombre total de pages
 */
function updateNavigationState(currentIndex, totalPages) {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const submitButton = document.getElementById('submit-survey');
    
    // Désactiver le bouton précédent sur la première page
    if (prevButton) {
        prevButton.disabled = currentIndex === 0;
    }
    
    // Gérer l'affichage du bouton suivant et du bouton soumettre
    if (nextButton && submitButton) {
        if (currentIndex === totalPages - 1) {
            // Dernière page : masquer le bouton suivant, afficher le bouton soumettre
            nextButton.style.display = 'none';
            submitButton.style.display = 'block';
        } else {
            // Pages intermédiaires : afficher le bouton suivant, masquer le bouton soumettre
            nextButton.style.display = 'block';
            submitButton.style.display = 'none';
        }
    }
}

/**
 * Met à jour la barre de progression
 * 
 * @param {number} currentIndex - Index de la page active
 */
function updateProgressBar(currentIndex) {
    const indicators = document.querySelectorAll('.progress-indicator');
    
    indicators.forEach((indicator, index) => {
        if (index === currentIndex) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
        
        if (index < currentIndex) {
            indicator.classList.add('completed');
        }
    });
    
    // Mettre à jour le pourcentage de progression
    const progressPercent = ((currentIndex + 1) / indicators.length) * 100;
    const progressText = document.querySelector('.progress-text');
    
    if (progressText) {
        progressText.textContent = `${Math.round(progressPercent)}%`;
    }
}

/**
 * Valide la page active
 * 
 * @returns {boolean} - True si la page est valide, sinon False
 */
function validateCurrentPage() {
    const currentIndex = getCurrentPageIndex();
    return validatePage(currentIndex);
}

/**
 * Valide une page spécifique
 * 
 * @param {number} pageIndex - Index de la page à valider
 * @returns {boolean} - True si la page est valide, sinon False
 */
function validatePage(pageIndex) {
    const pages = document.querySelectorAll('.survey-page');
    const page = pages[pageIndex];
    
    // Vérifier tous les champs requis
    const requiredInputs = page.querySelectorAll('[required]');
    let isValid = true;
    
    requiredInputs.forEach(input => {
        // Vérifier si le champ est vide
        if (!input.value) {
            isValid = false;
            
            // Mettre en évidence le champ invalide
            input.classList.add('is-invalid');
            
            // Créer un message d'erreur s'il n'existe pas déjà
            let errorMessage = input.nextElementSibling;
            if (!errorMessage || !errorMessage.classList.contains('invalid-feedback')) {
                errorMessage = document.createElement('div');
                errorMessage.classList.add('invalid-feedback');
                errorMessage.textContent = 'Ce champ est obligatoire.';
                input.parentNode.insertBefore(errorMessage, input.nextSibling);
            }
        } else {
            // Réinitialiser le style si le champ est valide
            input.classList.remove('is-invalid');
        }
    });
    
    // Si la page n'est pas valide, faire défiler jusqu'au premier champ invalide
    if (!isValid) {
        const firstInvalid = page.querySelector('.is-invalid');
        if (firstInvalid) {
            firstInvalid.focus();
            window.scrollTo({
                top: firstInvalid.offsetTop - 100,
                behavior: 'smooth'
            });
        }
    }
    
    return isValid;
}

/**
 * Valide toutes les pages du sondage
 * 
 * @returns {boolean} - True si toutes les pages sont valides, sinon False
 */
function validateAllPages() {
    const pages = document.querySelectorAll('.survey-page');
    let allValid = true;
    
    // Vérifier chaque page
    for (let i = 0; i < pages.length; i++) {
        if (!validatePage(i)) {
            allValid = false;
            
            // Naviguer vers la première page invalide
            navigateToPage(i);
            break;
        }
    }
    
    return allValid;
}
