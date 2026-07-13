function setupUpload() {

    const form = document.getElementById("upload-form");

    const fileInput = document.getElementById("file");
    const selectedFileText = document.getElementById("selected-file");

    const buttonText = document.getElementById("button-text");
    const loadingIndicator = document.getElementById("loading-indicator");

    const submitButton = form.querySelector('button[type="submit"]');
    const downloadWarning = document.getElementById("download-warning");
    const downloadBtn = document.getElementById("download-btn");
    const generalError = document.getElementById("general-error");
    const generalErrorMessage = document.getElementById("general-error-message");

    /*
    ----------------------------------------------------
    Reset file input on page load
    ----------------------------------------------------
    */

    window.addEventListener("load", () => {
        fileInput.value = "";
    });

    /*
    ----------------------------------------------------
    File selection
    ----------------------------------------------------
    */

    fileInput.addEventListener("change", () => {

        const file = fileInput.files[0];
        downloadWarning.classList.add("hidden");
        generalError.classList.add("hidden");

        if (file) {
            selectedFileText.textContent = `Ficheiro selecionado: ${file.name}`;
            submitButton.disabled = false;
            submitButton.classList.remove(
                "opacity-50",
                "cursor-not-allowed"
            );
            buttonText.textContent = "Processar Ficheiro";
        } else {
            selectedFileText.textContent = "Nenhum ficheiro selecionado";
        }
    });

    /*
    ----------------------------------------------------
    Upload
    ----------------------------------------------------
    */

    form.addEventListener("submit", async (event) => {

        event.preventDefault();
        if (fileInput.files.length === 0) {
            alert("Por favor selecione um ficheiro");
            return;
        }

        fileInput.disabled = true;
        fileInput.classList.add(
            "pointer-events-none",
            "cursor-not-allowed"
        );

        submitButton.disabled = true;

        submitButton.classList.add(
            "opacity-50",
            "cursor-not-allowed"
        );

        buttonText.textContent = "Carregando...";
        loadingIndicator.classList.remove("hidden");
        generalError.classList.add("hidden");

        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        try {

            const response = await fetch("/process", {
                method: "POST",
                body: formData
            });

            const result = await response.json();

            if (result.error) {
                throw new Error(
                    `${result.error} (Erro HTTP ${response.status})`
                );
            }

            /*
            -----------------------------
            Download button
            -----------------------------
            */

            if (result.ok) {
                downloadBtn.classList.remove("hidden");
                downloadWarning.classList.add("hidden");
            } else {
                downloadBtn.classList.add("hidden");
                downloadWarning.classList.remove("hidden");
            }

            /*
            -----------------------------
            Load report
            -----------------------------
            */

            loadReport(result);

            document
                .getElementById("report-container")
                .scrollIntoView({
                    behavior: "smooth"
                });

            buttonText.textContent = "Ficheiro Processado";

        }

        catch (error) {

            console.error(error);

            generalErrorMessage.textContent = error.message || "Erro inesperado";
            generalError.classList.remove("hidden");

            clearReport();

            submitButton.disabled = false;
            submitButton.classList.remove(
                "opacity-50",
                "cursor-not-allowed"
            );
            buttonText.textContent = "Processar Ficheiro";
        }

        finally {

            loadingIndicator.classList.add("hidden");
            fileInput.disabled = false;
            fileInput.classList.remove(
                "pointer-events-none",
                "cursor-not-allowed"
            );

        }

    });

}