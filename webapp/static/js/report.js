let classeTables = {};

/**
 * Initializes the report UI.
 * Safe to call both in the main application and in the downloaded report.
 */
function initReport() {
    restoreClasseTables();
    setupMainTabs();
    setupViewSelector();
    setupClasseSelector();

    // If this is an offline report, populate the classe selector.
    if (Object.keys(classeTables).length > 0) {
        populateClasseSelector();
    }
}

/**
 * Restores classe tables from the embedded JSON.
 * Used by the downloaded report.
 */
function restoreClasseTables() {
    const savedClasseData = document.getElementById("classe-data");

    if (!savedClasseData)
        return;

    try {
        classeTables = JSON.parse(savedClasseData.textContent);

        if (Object.keys(classeTables).length > 0) {
            populateClasseSelector();
        }

    } catch (e) {
        console.error("Erro ao restaurar dados:", e);
    }
}

/**
 * Called by upload.js after the backend returns.
 */
function loadReport(result) {

    const reportByInvariant = document.getElementById("all-errors");
    const warningsView = document.getElementById("warnings-view");
    const classeReportContent = document.getElementById("classe-report-content");

    reportByInvariant.innerHTML = result.table_all_errors;
    warningsView.innerHTML = result.warnings;

    classeTables = result.table_by_classe || {};

    persistClasseTables();

    populateClasseSelector();

    const classeSelector = document.getElementById("classe-selector");

    if (classeSelector.options.length > 0) {
        classeReportContent.innerHTML =
            classeTables[classeSelector.value];
    }

    document.getElementById("report-container")
        .classList.remove("hidden");

    updateViewSelectorUI(
        document.getElementById("view-selector").value
    );
}

/**
 * Removes all report data.
 * Used if upload fails.
 */
function clearReport() {

    classeTables = {};

    document.getElementById("all-errors").innerHTML = "";
    document.getElementById("warnings-view").innerHTML = "";
    document.getElementById("classe-report-content").innerHTML = "";

    const classeSelector =
        document.getElementById("classe-selector");

    if (classeSelector)
        classeSelector.innerHTML = "";

    const reportContainer =
        document.getElementById("report-container");

    if (reportContainer)
        reportContainer.classList.add("hidden");

    const saved =
        document.getElementById("classe-data");

    if (saved)
        saved.textContent = "{}";
}

/**
 * Persists classe tables inside the page.
 * Makes downloaded HTML self-contained.
 */
function persistClasseTables() {

    let dataScript =
        document.getElementById("classe-data");

    if (!dataScript) {

        dataScript = document.createElement("script");

        dataScript.id = "classe-data";
        dataScript.type = "application/json";

        document.body.appendChild(dataScript);
    }

    dataScript.textContent =
        JSON.stringify(classeTables);
}

/**
 * Populates the classe dropdown.
 */
function populateClasseSelector() {

    const classeSelector =
        document.getElementById("classe-selector");

    if (!classeSelector)
        return;

    classeSelector.innerHTML = "";

    Object.keys(classeTables).forEach(classe => {

        const option =
            document.createElement("option");

        option.value = classe;
        option.textContent = classe;

        classeSelector.appendChild(option);
    });

    if (classeSelector.options.length > 0) {

        document.getElementById("classe-report-content")
            .innerHTML = classeTables[
                classeSelector.value
            ];
    }
}

/**
 * View selector.
 */
function setupViewSelector() {

    const viewSelector =
        document.getElementById("view-selector");

    if (!viewSelector)
        return;

    viewSelector.addEventListener("change", () => {
        updateViewSelectorUI(viewSelector.value);
    });

    updateViewSelectorUI(viewSelector.value);
}

/**
 * Classe selector.
 */
function setupClasseSelector() {

    const classeSelector =
        document.getElementById("classe-selector");

    if (!classeSelector)
        return;

    classeSelector.addEventListener("change", () => {

        document.getElementById(
            "classe-report-content"
        ).innerHTML =
            classeTables[
                classeSelector.value
            ] || "";
    });
}

/**
 * Switches between "All errors" and "By classe".
 */
function updateViewSelectorUI(selectedView) {

    document
        .querySelectorAll(".report-view")
        .forEach(div => div.classList.add("hidden"));

    const selected =
        document.getElementById(selectedView);

    if (selected)
        selected.classList.remove("hidden");

    const wrapper =
        document.getElementById(
            "classe-selector-wrapper"
        );

    if (wrapper) {
        wrapper.classList.toggle(
            "hidden",
            selectedView !== "by-classe"
        );
    }
}

/**
 * Top tabs (Errors / Warnings)
 */
function setupMainTabs() {

    const tabs =
        document.querySelectorAll(
            "#report-tabs button"
        );

    tabs.forEach(btn => {

        btn.addEventListener("click", () => {

            tabs.forEach(b => {

                b.classList.remove(
                    "border-purple-600",
                    "text-gray-700",
                    "border-b-2"
                );

                b.classList.add(
                    "text-gray-500"
                );
            });

            btn.classList.add(
                "border-purple-600",
                "text-gray-700",
                "border-b-2"
            );

            document
                .getElementById("tab-errors")
                ?.classList.add("hidden");

            document
                .getElementById("tab-warnings")
                ?.classList.add("hidden");

            document
                .getElementById(
                    "tab-" + btn.dataset.tab
                )
                ?.classList.remove("hidden");
        });

    });
}