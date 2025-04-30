document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('file');
    const selectedFileText = document.getElementById('selected-file');
    const buttonText = document.getElementById('button-text');
    const loadingIndicator = document.getElementById('loading-indicator');
    const reportContainer = document.getElementById('report-container');
    const reportContent = document.getElementById('report-content');

    // Update the selected file display
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            selectedFileText.textContent = `Selecionado: ${fileInput.files[0].name}`;
            selectedFileText.classList.remove('hidden');
        } else {
            selectedFileText.classList.add('hidden');
        }
    });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();

        // TODO: temporário
        if (fileInput.files.length === 0) {
            alert('Por favor selcione um ficheiro');
            return;
        }

        // Show loading state
        buttonText.textContent = 'Carregando...';
        loadingIndicator.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const result = await response.json();

            if (result.error) {
                throw new Error(result.error);
            }

            // Display the result
            if (result.html) {
                reportContent.innerHTML = result.html;
                reportContainer.classList.remove('hidden');
                // Scroll to result
                reportContainer.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error processing file:', error);
            reportContent.innerHTML = `
                <div class="p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
                    <p class="font-medium">Error</p>
                    <p>${error.message}</p>
                </div>
            `;
            reportContainer.classList.remove('hidden');

        } finally {
            // Reset button state
            buttonText.textContent = 'Process File';
            loadingIndicator.classList.add('hidden');
        }
    });
});
