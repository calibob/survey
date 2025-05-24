/**
 * Gestion de la logique conditionnelle des questions dans les sondages
 *
 * Ce script permet d'afficher ou masquer des questions en fonction des réponses
 * aux questions précédentes, selon les conditions définies.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser les questions conditionnelles
    initConditionalQuestions();
    
    // Configurer les déclencheurs de conditions
    setupConditionTriggers();
});

/**
 * Initialise les questions conditionnelles en les masquant par défaut
 */
function initConditionalQuestions() {
    const conditionalQuestions = document.querySelectorAll('.conditional-question');
    
    // Masquer toutes les questions conditionnelles par défaut
    conditionalQuestions.forEach(question => {
        question.style.display = 'none';
    });
    
    // Appliquer les conditions initiales basées sur les valeurs par défaut
    document.querySelectorAll('.trigger-condition[checked]').forEach(trigger => {
        evaluateConditions(trigger);
    });
}

/**
 * Configure les déclencheurs pour l'évaluation des conditions
 */
function setupConditionTriggers() {
    // Sélectionner tous les inputs qui peuvent déclencher des conditions
    const triggers = document.querySelectorAll('.trigger-condition');
    
    triggers.forEach(trigger => {
        // Déterminer le type d'événement à écouter selon le type d'input
        const eventType = getEventTypeForInput(trigger);
        
        // Ajouter l'écouteur d'événement
        trigger.addEventListener(eventType, function() {
            evaluateConditions(this);
        });
    });
}

/**
 * Détermine le type d'événement approprié pour un input
 * 
 * @param {HTMLElement} input - L'élément input
 * @returns {string} - Le type d'événement à écouter
 */
function getEventTypeForInput(input) {
    const inputType = input.type;
    
    switch (inputType) {
        case 'radio':
        case 'checkbox':
            return 'change';
        case 'text':
        case 'number':
        case 'date':
            return 'input';
        case 'select-one':
        case 'select-multiple':
            return 'change';
        default:
            if (input.tagName === 'TEXTAREA') {
                return 'input';
            }
            return 'change';
    }
}

/**
 * Évalue toutes les conditions liées à un déclencheur
 * 
 * @param {HTMLElement} trigger - L'élément qui a déclenché l'évaluation
 */
function evaluateConditions(trigger) {
    // Trouver l'ID de la question contenant ce déclencheur
    const questionContainer = trigger.closest('.card');
    if (!questionContainer) return;
    
    const questionId = questionContainer.id.replace('question-container-', '');
    
    // Trouver toutes les questions conditionnelles qui dépendent de cette question
    const dependentQuestions = document.querySelectorAll(`.conditional-question[data-depends-on="${questionId}"]`);
    
    dependentQuestions.forEach(dependentQuestion => {
        const conditionOperator = dependentQuestion.dataset.conditionOperator;
        const conditionValue = dependentQuestion.dataset.conditionValue;
        
        // Évaluer la condition
        const isConditionMet = evaluateCondition(trigger, conditionOperator, conditionValue);
        
        // Afficher ou masquer la question conditionnelle
        if (isConditionMet) {
            dependentQuestion.style.display = 'block';
            // Activer les inputs pour qu'ils soient inclus dans la soumission du formulaire
            toggleInputs(dependentQuestion, true);
        } else {
            dependentQuestion.style.display = 'none';
            // Désactiver les inputs pour qu'ils ne soient pas inclus dans la soumission du formulaire
            toggleInputs(dependentQuestion, false);
        }
        
        // Mettre à jour les numéros de questions visibles
        updateQuestionNumbers();
    });
}

/**
 * Évalue une condition spécifique
 * 
 * @param {HTMLElement} trigger - L'élément déclencheur
 * @param {string} operator - L'opérateur de la condition (equals, not_equals, contains, etc.)
 * @param {string} value - La valeur à comparer
 * @returns {boolean} - True si la condition est remplie, sinon False
 */
function evaluateCondition(trigger, operator, value) {
    let triggerValue = getTriggerValue(trigger);
    
    switch (operator) {
        case 'equals':
            return triggerValue === value;
        case 'not_equals':
            return triggerValue !== value;
        case 'contains':
            return typeof triggerValue === 'string' && triggerValue.includes(value);
        case 'greater_than':
            return parseFloat(triggerValue) > parseFloat(value);
        case 'less_than':
            return parseFloat(triggerValue) < parseFloat(value);
        case 'checked':
            return trigger.checked;
        case 'not_checked':
            return !trigger.checked;
        case 'any_selected':
            // Pour les checkboxes, vérifier si au moins une option est sélectionnée
            return document.querySelectorAll(`input[name="${trigger.name}"]:checked`).length > 0;
        default:
            return false;
    }
}

/**
 * Récupère la valeur d'un élément déclencheur
 * 
 * @param {HTMLElement} trigger - L'élément déclencheur
 * @returns {string} - La valeur de l'élément
 */
function getTriggerValue(trigger) {
    const inputType = trigger.type;
    
    switch (inputType) {
        case 'radio':
            // Pour les boutons radio, récupérer la valeur du bouton sélectionné
            const checkedRadio = document.querySelector(`input[name="${trigger.name}"]:checked`);
            return checkedRadio ? checkedRadio.value : '';
        case 'checkbox':
            // Pour les cases à cocher, récupérer toutes les valeurs cochées
            if (trigger.checked) {
                return trigger.value;
            }
            return '';
        case 'select-multiple':
            // Pour les select multiple, récupérer un tableau de valeurs
            return Array.from(trigger.selectedOptions).map(option => option.value).join(',');
        default:
            // Pour les autres types, récupérer simplement la valeur
            return trigger.value;
    }
}

/**
 * Active ou désactive les inputs dans une question conditionnelle
 * 
 * @param {HTMLElement} questionContainer - Le conteneur de la question
 * @param {boolean} enable - True pour activer, False pour désactiver
 */
function toggleInputs(questionContainer, enable) {
    const inputs = questionContainer.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.disabled = !enable;
        
        // Si on désactive, réinitialiser les valeurs
        if (!enable) {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
            
            // Supprimer la classe d'invalidation si présente
            input.classList.remove('is-invalid');
            
            // Supprimer les messages d'erreur
            const feedback = input.nextElementSibling;
            if (feedback && feedback.classList.contains('invalid-feedback')) {
                feedback.remove();
            }
        }
    });
}

/**
 * Met à jour les numéros de questions visibles
 */
function updateQuestionNumbers() {
    // Récupérer toutes les questions visibles
    const visibleQuestions = Array.from(document.querySelectorAll('.card')).filter(
        card => card.style.display !== 'none'
    );
    
    // Mettre à jour les numéros
    visibleQuestions.forEach((question, index) => {
        const numberElement = question.querySelector('.card-header h5');
        if (numberElement) {
            // Extraire le texte après le numéro
            const text = numberElement.textContent;
            const dotIndex = text.indexOf('.');
            if (dotIndex !== -1) {
                const questionText = text.substring(dotIndex + 1);
                numberElement.textContent = `${index + 1}.${questionText}`;
            }
        }
    });
}
