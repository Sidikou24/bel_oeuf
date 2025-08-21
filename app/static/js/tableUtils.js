// tableUtils.js
// Fonctions génériques pour filtrer et paginer les tableaux HTML

/**
 * Filtre les lignes d'un tableau selon la valeur d'un champ de recherche et une colonne donnée.
 * @param {string} tableSelector - Sélecteur CSS du tableau
 * @param {string} inputSelector - Sélecteur CSS du champ de recherche
 * @param {number} colIndex - Index de la colonne à filtrer (0 = première colonne)
 */
function filtrerTableParColonne(tableSelector, inputSelector, colIndex) {
    const input = document.querySelector(inputSelector);
    const table = document.querySelector(tableSelector);
    if (!input || !table) return;
    input.addEventListener('keyup', function() {
        const filter = input.value.toLowerCase();
        const trs = table.querySelectorAll('tbody tr');
        trs.forEach(tr => {
            const td = tr.querySelectorAll('td')[colIndex];
            if (td && td.textContent.toLowerCase().includes(filter)) {
                tr.style.display = '';
            } else {
                tr.style.display = 'none';
            }
        });
    });
}

/**
 * Paginer un tableau HTML côté client
 * @param {string} tableSelector - Sélecteur CSS du tableau
 * @param {number} rowsPerPage - Nombre de lignes par page
 * @param {string} paginationContainerSelector - Sélecteur CSS du conteneur de pagination
 */
function paginerTable(tableSelector, rowsPerPage, paginationContainerSelector) {
    const table = document.querySelector(tableSelector);
    const paginationContainer = document.querySelector(paginationContainerSelector);
    if (!table || !paginationContainer) return;
    const trs = Array.from(table.querySelectorAll('tbody tr'));
    let currentPage = 1;
    const totalPages = Math.ceil(trs.length / rowsPerPage);

    function showPage(page) {
        trs.forEach((tr, i) => {
            tr.style.display = (i >= (page - 1) * rowsPerPage && i < page * rowsPerPage) ? '' : 'none';
        });
        renderPagination(page);
    }

    function renderPagination(page) {
        paginationContainer.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = 'btn btn-sm' + (i === page ? ' btn-primary' : ' btn-outline');
            btn.onclick = () => {
                currentPage = i;
                showPage(currentPage);
            };
            paginationContainer.appendChild(btn);
        }
    }

    showPage(currentPage);
}

// Export des fonctions pour usage global
window.filtrerTableParColonne = filtrerTableParColonne;
window.paginerTable = paginerTable;
