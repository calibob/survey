/**
 * Gestion de la logique conditionnelle pour les sondages
 * 
 * Ce script permet de gérer l'affichage conditionnel des questions
 * en fonction des réponses précédentes des utilisateurs.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser le système de questions conditionnelles
    initConditionalLogic();
    
    // Ajouter des écouteurs d'événements sur toutes les questions qui peuvent déclencher des conditions
    setupTriggerListeners();
});

/**
 * Initialise la logique conditionnelle en masquant les questions 
 * conditionnelles au chargement de la page
 */
function initConditionalLogic() {
    // Sélectionner toutes les questions conditionnelles
    const conditionalQuestions = document.querySelectorAll('.conditional-question');
    
    conditionalQuestions.forEach(question => {
        // Au chargement initial, masquer toutes les questions conditionnelles
        question.style.display = 'none';
        
        // Marquer les champs de ces questions comme non requis temporairement
        const requiredInputs = question.querySelectorAll('[required]');
        requiredInputs.forEach(input => {
            input.dataset.required = true; // Stocker l'état requis original
            input.required = false; // Désactiver le required tant que la question est masquée
        });
    });
    
    // Vérifier les conditions initiales (au cas où certaines valeurs sont pré-remplies)
    checkAllConditions();
}

/**
 * Configure les écouteurs d'événements sur les éléments qui peuvent 
 * déclencher des changements dans les conditions
 */
function setupTriggerListeners() {
    // Sélectionner tous les éléments qui peuvent déclencher des conditions
    const triggerElements = document.querySelectorAll('.trigger-condition');
    
    triggerElements.forEach(element => {
        // Déterminer le type d'événement en fonction du type d'élément
        let eventType = 'change'; // Par défaut pour les selects, radios, checkboxes
        
        if (element.tagName === 'INPUT') {
            if (element.type === 'text' || element.type === 'number' || element.type === 'date') {
                eventType = 'input'; // Pour les champs texte, utiliser l'événement input
            }
        }
        
        // Ajouter l'écouteur d'événement
        element.addEventListener(eventType, function() {
            checkAllConditions();
        });
    });
}

/**
 * Vérifie toutes les conditions pour décider quelles questions afficher ou masquer
 */
function checkAllConditions() {
    // Sélectionner toutes les questions conditionnelles
    const conditionalQuestions = document.querySelectorAll('.conditional-question');
    
    conditionalQuestions.forEach(question => {
        // Extraire les informations de condition
        const dependsOnId = question.dataset.dependsOn;
        const operator = question.dataset.conditionOperator;
        const expectedValue = question.dataset.conditionValue;
        
        // Vérifier si la condition est satisfaite
        const isSatisfied = checkCondition(dependsOnId, operator, expectedValue);
        
        // Afficher ou masquer la question en fonction du résultat
        if (isSatisfied) {
            showQuestion(question);
        } else {
            hideQuestion(question);
        }
    });
}

/**
 * Vérifie si une condition spécifique est satisfaite
 * 
 * @param {string} dependsOnId - ID de la question dont dépend la condition
 * @param {string} operator - Opérateur de la condition (equals, not_equals, etc.)
 * @param {string} expectedValue - Valeur attendue
 * @returns {boolean} - True si la condition est satisfaite, sinon False
 */
function checkCondition(dependsOnId, operator, expectedValue) {
    // Récupérer la valeur actuelle de la question dont dépend la condition
    const currentValue = getCurrentValue(dependsOnId);
    
    // Vérifier la condition en fonction de l'opérateur
    switch (operator) {
        case 'equals':
            return currentValue === expectedValue;
        
        case 'not_equals':
            return currentValue !== expectedValue;
        
        case 'contains':
            return currentValue.includes(expectedValue);
        
        case 'greater_than':
            return parseFloat(currentValue) > parseFloat(expectedValue);
        
        case 'less_than':
            return parseFloat(currentValue) < parseFloat(expectedValue);
        
        case 'selected':
            // Pour les questions à choix multiples
            return currentValue.includes(expectedValue);
        
        default:
            console.warn('Opérateur de condition non reconnu:', operator);
            return false;
    }
}

/**
 * Récupère la valeur actuelle d'une question
 * 
 * @param {string} questionId - ID de la question
 * @returns {string} - Valeur actuelle
 */
function getCurrentValue(questionId) {
    // Trouver la question par son ID
    const questionContainer = document.getElementById('question-' + questionId);
    
    if (!questionContainer) {
        console.warn('Question non trouvée:', questionId);
        return '';
    }
    
    // Déterminer le type de question
    const radioInputs = questionContainer.querySelectorAll('input[type="radio"]:checked');
    const checkboxInputs = questionContainer.querySelectorAll('input[type="checkbox"]:checked');
    const selectInputs = questionContainer.querySelectorAll('select');
    const textInputs = questionContainer.querySelectorAll('input[type="text"], textarea, input[type="number"], input[type="date"]');
    
    // Récupérer la valeur en fonction du type
    if (radioInputs.length > 0) {
        return radioInputs[0].value;
    } else if (checkboxInputs.length > 0) {
        // Pour les cases à cocher, on peut avoir plusieurs valeurs
        return Array.from(checkboxInputs).map(input => input.value).join(',');
    } else if (selectInputs.length > 0) {
        return selectInputs[0].value;
    } else if (textInputs.length > 0) {
        return textInputs[0].value;
    }
    
    return '';
}

/**
 * Affiche une question conditionnelle et réactive ses champs requis
 * 
 * @param {HTMLElement} question - Élément de question à afficher
 */
function showQuestion(question) {
    question.style.display = 'block';
    
    // Réactiver les champs requis
    const requiredInputs = question.querySelectorAll('[data-required="true"]');
    requiredInputs.forEach(input => {
        input.required = true;
    });
    
    // Animation d'apparition
    question.style.opacity = 0;
    setTimeout(() => {
        question.style.transition = 'opacity 0.3s ease';
        question.style.opacity = 1;
    }, 10);
}

/**
 * Masque une question conditionnelle et désactive ses champs requis
 * 
 * @param {HTMLElement} question - Élément de question à masquer
 */
function hideQuestion(question) {
    // Animation de disparition
    question.style.transition = 'opacity 0.3s ease';
    question.style.opacity = 0;
    
    // Désactiver les champs requis
    const requiredInputs = question.querySelectorAll('[required]');
    requiredInputs.forEach(input => {
        input.required = false;
    });
    
    // Masquer la question après l'animation
    setTimeout(() => {
        question.style.display = 'none';
        
        // Réinitialiser les valeurs des champs
        const inputs = question.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            if (input.type === 'checkbox' || input.type === 'radio') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
    }, 300);
}

/**
 * Fonction d'aide pour déboguer les conditions
 * 
 * @param {string} message - Message à afficher
 */
function debugConditional(message) {
    if (window.surveyDebug === true) {
        console.log('Survey Debug:', message);
    }
}
