let classeTables = {};

document.addEventListener('DOMContentLoaded', () => {
    const reportByInvariant = document.getElementById('all-errors');
    const classeReportContent = document.getElementById('classe-report-content');
    const classeSelector = document.getElementById('classe-selector');
    const warningsView = document.getElementById('warnings-view');

    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const selectedFileText = document.getElementById('selected-file');
    const buttonText = document.getElementById('button-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const reportContainer = document.getElementById('report-container');

    const downloadWarning = document.getElementById('download-warning');
    const downloadBtn = document.getElementById('download-btn');
    const generalError = document.getElementById('general-error');
    const generalErrorMessage = document.getElementById('general-error-message');

    const viewSelector = document.getElementById('view-selector');
    const submitButton = form.querySelector('button[type="submit"]');

    // Reset file input on page load
    window.addEventListener('load', () => {
        if (fileInput) fileInput.value = '';
    });

    // File input change handler
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];

        // Reset banners
        downloadWarning.classList.add('hidden');
        generalError.classList.add('hidden');

        if (file) {
            selectedFileText.textContent = `Ficheiro selecionado: ${file.name}`;
            selectedFileText.classList.remove('hidden');

            // Enable submit
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Processar Ficheiro';
        } else {
            selectedFileText.textContent = 'Nenhum ficheiro selecionado';
            selectedFileText.classList.remove('hidden');
        }
    });

    setupMainTabs();

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        if (fileInput.files.length === 0) {
            alert('Por favor selecione um ficheiro');
            return;
        }

        buttonText.textContent = 'Carregando...';
        loadingIndicator.classList.remove('hidden');
        generalError.classList.add('hidden');

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

            // Setup classe tables
            if (result.table_by_classe && result.table_by_invariant && result.warnings) {
                reportByInvariant.innerHTML = result.table_by_invariant;
                warningsView.innerHTML = result.warnings;
                classeTables = result.table_by_classe;

                classeSelector.innerHTML = '';
                Object.keys(classeTables).forEach(classe => {
                    const option = document.createElement('option');
                    option.value = classe;
                    option.textContent = classe;
                    classeSelector.appendChild(option);
                });

                // Show first classe by default
                classeReportContent.innerHTML = classeTables[classeSelector.value];

                document.querySelectorAll('.report-view').forEach(div => div.classList.add('hidden'));
                document.getElementById(viewSelector.value).classList.remove('hidden');
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
            generalErrorMessage.textContent = error.message || 'Erro inesperado';
            generalError.classList.remove('hidden');

            // Reset report display data
            reportContainer.classList.add('hidden');
            classeReportContent.innerHTML = '';
            reportByInvariant.innerHTML = '';
            classeTables = {};

            // Re-enable the button on error
            submitButton.disabled = false;
            submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
            buttonText.textContent = 'Processar Ficheiro';
        } finally {
            loadingIndicator.classList.add('hidden');
        }
    });

    // Handle view switching
    viewSelector.addEventListener('change', () => {
        updateViewSelectorUI(viewSelector.value);
    });
    updateViewSelectorUI(viewSelector.value);

    // Handle classe selection within classe view
    classeSelector.addEventListener('change', () => {
        const selectedClasse = classeSelector.value;
        classeReportContent.innerHTML = classeTables[selectedClasse];
    });
});

function updateViewSelectorUI(selectedView) {
    document.querySelectorAll('.report-view').forEach(div => div.classList.add('hidden'));
    document.getElementById(selectedView).classList.remove('hidden');

    document.getElementById('classe-selector-wrapper')
        .classList.toggle('hidden', selectedView !== 'by-classe');
}

function setupMainTabs() {
    document.querySelectorAll('#report-tabs button').forEach(btn => {
        btn.addEventListener('click', () => {
            // reset styles on all tabs
            document.querySelectorAll('#report-tabs button').forEach(b => {
                b.classList.remove('border-purple-600', 'text-gray-700', 'border-b-2');
                b.classList.add('text-gray-500');
            });

            // activate clicked tab
            btn.classList.add('border-purple-600', 'text-gray-700', 'border-b-2');

            // switch content
            document.getElementById('tab-errors').classList.add('hidden');
            document.getElementById('tab-warnings').classList.add('hidden');
            document.getElementById('tab-' + btn.dataset.tab).classList.remove('hidden');
        });
    });
}
