/**
 * Gestion de la prévisualisation des sondages
 * 
 * Ce script permet de prévisualiser le sondage selon différents appareils
 * et de simuler la soumission des réponses.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les boutons de prévisualisation
    initPreviewButtons();
    
    // Simuler les interactions utilisateur dans la prévisualisation
    setupInteractivePreview();
});

/**
 * Initialise les boutons de prévisualisation pour les différents appareils
 */
function initPreviewButtons() {
    const deviceButtons = document.querySelectorAll('.preview-type-radio');
    const previewContainer = document.querySelector('.preview-container');
    
    if (!deviceButtons.length || !previewContainer) return;
    
    deviceButtons.forEach(button => {
        button.addEventListener('change', function() {
            // Supprimer toutes les classes de taille
            previewContainer.classList.remove('desktop-preview', 'tablet-preview', 'mobile-preview');
            
            // Ajouter la classe correspondante au bouton sélectionné
            previewContainer.classList.add(`${this.value}-preview`);
            
            // Mettre à jour l'URL avec le paramètre device
            const url = new URL(window.location.href);
            url.searchParams.set('device', this.value);
            window.history.replaceState({}, '', url.toString());
        });
    });
}

/**
 * Configure les interactions pour la prévisualisation
 */
function setupInteractivePreview() {
    if (!document.querySelector('.preview-container')) return;
    
    // Simuler le comportement des questions conditionnelles
    setupConditionalSimulation();
    
    // Simuler le comportement des sauts de page
    setupPageBreakSimulation();
    
    // Simuler la soumission du formulaire
    setupSubmissionSimulation();
}

/**
 * Simule le comportement des questions conditionnelles dans la prévisualisation
 */
function setupConditionalSimulation() {
    // Sélectionner toutes les questions conditionnelles dans la prévisualisation
    const conditionalQuestions = document.querySelectorAll('.preview-container .conditional-question');
    
    // Ajouter un indicateur visuel aux questions conditionnelles
    conditionalQuestions.forEach(question => {
        const badge = document.createElement('span');
        badge.classList.add('badge', 'bg-warning', 'text-dark', 'conditional-badge');
        badge.textContent = 'Question conditionnelle';
        badge.style.position = 'absolute';
        badge.style.top = '10px';
        badge.style.right = '10px';
        badge.style.zIndex = '10';
        
        // Si la question a un en-tête, l'ajouter là, sinon à la question elle-même
        const header = question.querySelector('.card-header');
        if (header) {
            header.style.position = 'relative';
            header.appendChild(badge);
        } else {
            question.style.position = 'relative';
            question.appendChild(badge);
        }
    });
    
    // Ajouter des événements aux options qui peuvent déclencher des conditions
    const radioInputs = document.querySelectorAll('.preview-container input[type="radio"]');
    const checkboxInputs = document.querySelectorAll('.preview-container input[type="checkbox"]');
    
    [...radioInputs, ...checkboxInputs].forEach(input => {
        input.addEventListener('change', function() {
            // Simuler un changement aléatoire dans l'affichage des questions conditionnelles
            simulateConditionalVisibility();
        });
    });
}

/**
 * Simule aléatoirement la visibilité des questions conditionnelles
 */
function simulateConditionalVisibility() {
    const conditionalQuestions = document.querySelectorAll('.preview-container .conditional-question');
    
    conditionalQuestions.forEach(question => {
        // Probabilité aléatoire de montrer ou cacher la question
        const shouldShow = Math.random() > 0.5;
        
        if (shouldShow) {
            question.style.display = 'block';
            question.style.opacity = '1';
            
            // Mettre à jour le badge
            const badge = question.querySelector('.conditional-badge');
            if (badge) {
                badge.classList.remove('bg-secondary');
                badge.classList.add('bg-success');
                badge.textContent = 'Condition remplie';
            }
        } else {
            question.style.opacity = '0.5';
            
            // Mettre à jour le badge
            const badge = question.querySelector('.conditional-badge');
            if (badge) {
                badge.classList.remove('bg-success');
                badge.classList.add('bg-secondary');
                badge.textContent = 'Condition non remplie';
            }
        }
    });
    
    // Afficher un message de prévisualisation
    const previewMessage = document.getElementById('preview-message');
    if (previewMessage) {
        previewMessage.textContent = 'Les questions conditionnelles apparaissent ou disparaissent en fonction des réponses';
        previewMessage.style.display = 'block';
        
        // Masquer le message après 3 secondes
        setTimeout(() => {
            previewMessage.style.opacity = '0';
            setTimeout(() => {
                previewMessage.style.display = 'none';
                previewMessage.style.opacity = '1';
            }, 500);
        }, 3000);
    }
}

/**
 * Simule le comportement des sauts de page dans la prévisualisation
 */
function setupPageBreakSimulation() {
    // Mettre en évidence les sauts de page
    const pageBreaks = document.querySelectorAll('.preview-container .page-break');
    
    pageBreaks.forEach(pageBreak => {
        // Ajouter un indicateur visuel
        const indicator = document.createElement('div');
        indicator.classList.add('page-break-indicator');
        indicator.innerHTML = '<i class="fas fa-file-alt"></i> Nouvelle page';
        indicator.style.textAlign = 'center';
        indicator.style.padding = '5px';
        indicator.style.backgroundColor = '#f8f9fa';
        indicator.style.borderRadius = '4px';
        indicator.style.marginBottom = '10px';
        
        pageBreak.prepend(indicator);
    });
    
    // Simuler la navigation entre les pages
    const nextButtons = document.querySelectorAll('.preview-container .btn-next-page');
    const prevButtons = document.querySelectorAll('.preview-container .btn-prev-page');
    
    [...nextButtons, ...prevButtons].forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Simuler le changement de page
            const previewMessage = document.getElementById('preview-message');
            if (previewMessage) {
                previewMessage.textContent = this.classList.contains('btn-next-page') ? 
                    'Navigation vers la page suivante' : 'Navigation vers la page précédente';
                previewMessage.style.display = 'block';
                
                // Masquer le message après 2 secondes
                setTimeout(() => {
                    previewMessage.style.opacity = '0';
                    setTimeout(() => {
                        previewMessage.style.display = 'none';
                        previewMessage.style.opacity = '1';
                    }, 500);
                }, 2000);
            }
        });
    });
}

/**
 * Simule la soumission du formulaire dans la prévisualisation
 */
function setupSubmissionSimulation() {
    const submitButton = document.querySelector('.preview-container .btn-primary');
    
    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Créer une boîte de dialogue de confirmation
            const confirmDialog = document.createElement('div');
            confirmDialog.classList.add('modal', 'fade');
            confirmDialog.id = 'previewConfirmModal';
            confirmDialog.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Prévisualisation</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <p>En mode prévisualisation, les réponses ne sont pas enregistrées.</p>
                            <p>Dans un sondage réel, les réponses seraient maintenant soumises et l'utilisateur serait redirigé vers la page de remerciement.</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                            <a href="#" class="btn btn-primary" id="showThankYouPage">Voir la page de remerciement</a>
                        </div>
                    </div>
                </div>
            `;
            
            // Ajouter la boîte de dialogue au document
            document.body.appendChild(confirmDialog);
            
            // Créer et afficher la modal avec Bootstrap
            const modal = new bootstrap.Modal(confirmDialog);
            modal.show();
            
            // Gérer le clic sur le bouton "Voir la page de remerciement"
            document.getElementById('showThankYouPage').addEventListener('click', function() {
                // Récupérer l'ID du sondage depuis l'URL
                const urlParams = new URLSearchParams(window.location.search);
                const surveyId = urlParams.get('survey_id') || window.location.pathname.split('/')[2];
                
                // Rediriger vers la page de remerciement
                window.location.href = `/surveys/${surveyId}/thankyou/`;
            });
            
            // Supprimer la boîte de dialogue lorsqu'elle est fermée
            confirmDialog.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(confirmDialog);
            });
        });
    }
}
