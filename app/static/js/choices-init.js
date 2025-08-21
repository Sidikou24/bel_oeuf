// Ajoute Choices.js pour les selects avec recherche
// https://github.com/Choices-js/Choices

// Initialisation pour le formulaire de création
window.addEventListener('DOMContentLoaded', function() {
    if (window.Choices) {
        const fournisseurSelect = document.querySelector('select[name="fournisseur_id"]');
        if (fournisseurSelect) {
            new Choices(fournisseurSelect, { searchEnabled: true, itemSelectText: '' });
        }
        const matiereSelect = document.querySelector('select[name="matiere_id"]');
        if (matiereSelect) {
            new Choices(matiereSelect, { searchEnabled: true, itemSelectText: '' });
        }
        // Pour le modal d'édition
        const editFournisseurSelect = document.getElementById('editFournisseurId');
        if (editFournisseurSelect) {
            new Choices(editFournisseurSelect, { searchEnabled: true, itemSelectText: '' });
        }
        const editMatiereSelect = document.getElementById('editMatiereId');
        if (editMatiereSelect) {
            new Choices(editMatiereSelect, { searchEnabled: true, itemSelectText: '' });
        }
    }
});
