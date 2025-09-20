let entityTables = {};

document.addEventListener('DOMContentLoaded', () => {
    const reportByInvariant = document.getElementById('by-invariant');
    const entityReportContent = document.getElementById('entity-report-content');
    const entitySelector = document.getElementById('entity-selector');

    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const selectedFileText = document.getElementById('selected-file');
    const buttonText = document.getElementById('button-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const reportContainer = document.getElementById('report-container');

    const downloadWarning = document.getElementById('download-warning');
    const downloadBtn = document.getElementById('download-btn');
    const generalError = document.getElementById('general-error');

    window.addEventListener('load', function () {
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
        }
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];

        // When the file changes, the error "banners" are reset
        downloadWarning.classList.add('hidden');
        generalError.classList.add('hidden');

        if (file) {
            selectedFileText.textContent = `Ficheiro selecionado: ${file.name}`;
            selectedFileText.classList.remove('hidden');

            // Re-enable the submit button when a new file is selected
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Processar Ficheiro';
        } else {
            selectedFileText.textContent = 'Nenhum ficheiro selecionado';
            selectedFileText.classList.remove('hidden');
        }
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (fileInput.files.length === 0) {
            alert('Por favor selecione um ficheiro');
            return;
        }

        buttonText.textContent = 'Carregando...';
        loadingIndicator.classList.remove('hidden');
        generalError.classList.add('hidden');

        const submitButton = form.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.classList.add('opacity-50', 'cursor-not-allowed');

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const result = await response.json();
            if (result.error) throw new Error(result.error);

            if (result.ok) {
                downloadBtn.classList.remove('hidden');
                downloadWarning.classList.add('hidden');
            } else {
                downloadBtn.classList.add('hidden');
                downloadWarning.classList.remove('hidden');
            }

            // Setup entity tables
            if (result.table_by_entity && result.table_by_invariant) {
                reportByInvariant.innerHTML = result.table_by_invariant;
                entityTables = result.table_by_entity;

                entitySelector.innerHTML = '';
                Object.keys(entityTables).forEach(entity => {
                    const option = document.createElement('option');
                    option.value = entity;
                    option.textContent = entity;
                    entitySelector.appendChild(option);
                });

                // Show first entity by default
                entityReportContent.innerHTML = entityTables[entitySelector.value];

                document.querySelectorAll('.report-view').forEach(div => div.classList.add('hidden'));
                document.getElementById(document.getElementById('view-selector').value).classList.remove('hidden');

            } else {
                throw new Error(result.error || 'Erro ao processar o ficheiro.');
            }

            reportContainer.classList.remove('hidden');
            reportContainer.scrollIntoView({ behavior: 'smooth' });
            buttonText.textContent = 'Ficheiro Processado';
            submitButton.disabled = true;
            submitButton.classList.add('opacity-50', 'cursor-not-allowed');

        } catch (error) {

            console.error('Erro:', error);
            const generalErrorMessage = document.getElementById('general-error-message');
            generalErrorMessage.textContent = error.message || 'Erro inesperado';
            generalError.classList.remove('hidden');

            // Reset report display data
            reportContainer.classList.add('hidden');
            entityReportContent.innerHTML = '';
            reportByInvariant.innerHTML = '';
            entityTables = {};

            // Re-enable the button on error
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Processar Ficheiro';
        } finally {
            loadingIndicator.classList.add('hidden');
        }

    });

    // Handle view switching
    const viewSelector = document.getElementById('view-selector');
    viewSelector.addEventListener('change', () => {
        updateViewSelectorUI(viewSelector.value);
    });
    updateViewSelectorUI(viewSelector.value);

    // Handle entity selection within entity view
    entitySelector.addEventListener('change', () => {
        const selectedEntity = entitySelector.value;
        entityReportContent.innerHTML = entityTables[selectedEntity];
    });
});

function updateViewSelectorUI(selectedView) {
    document.querySelectorAll('.report-view').forEach(div => div.classList.add('hidden'));
    document.getElementById(selectedView).classList.remove('hidden');

    document.getElementById('entity-selector-wrapper')
        .classList.toggle('hidden', selectedView !== 'by-entity');
}
