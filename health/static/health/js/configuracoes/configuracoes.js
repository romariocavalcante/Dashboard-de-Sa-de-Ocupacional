const STORAGE_KEY = "health_settings_v1";

const settingFields = document.querySelectorAll("[data-setting]");
const saveAllButton = document.querySelector("#save-all-settings");
const resetButton = document.querySelector("#reset-settings");
const saveCardButtons = document.querySelectorAll(".btn-save-card");
const feedbackElement = document.querySelector("#save-feedback");
const toastElement = document.querySelector("#settings-toast");

function readCurrentValues() {
    const values = {};
    settingFields.forEach((field) => {
        values[field.name] = field.type === "checkbox" ? field.checked : field.value;
    });
    return values;
}

function writeValues(values) {
    settingFields.forEach((field) => {
        if (!(field.name in values)) return;

        if (field.type === "checkbox") {
            field.checked = Boolean(values[field.name]);
        } else {
            field.value = values[field.name];
        }
    });
}

function defaultValues() {
    const values = {};
    settingFields.forEach((field) => {
        if (field.type === "checkbox") {
            values[field.name] = field.dataset.default === "true";
        } else {
            values[field.name] = field.dataset.default || "";
        }
    });
    return values;
}

function validate(values) {
    const aviso90 = Number(values.janela_aviso_90 || 0);
    const aviso60 = Number(values.janela_aviso_60 || 0);
    const cid = String(values.cid_prioritario || "").trim();

    if (!cid) {
        return "Informe um CID prioritário.";
    }

    if (aviso90 <= aviso60) {
        return "A janela principal deve ser maior que a secundária.";
    }

    return "";
}

function showToast(message) {
    if (!toastElement) return;
    toastElement.textContent = message;
    toastElement.classList.add("show");
    setTimeout(() => {
        toastElement.classList.remove("show");
    }, 2200);
}

function setFeedback(message, isError = false) {
    if (!feedbackElement) return;
    feedbackElement.textContent = message;
    feedbackElement.style.color = isError ? "#b91c1c" : "#2563eb";
}

function saveSettings() {
    const values = readCurrentValues();
    const error = validate(values);

    if (error) {
        setFeedback(error, true);
        showToast(error);
        return false;
    }

    localStorage.setItem(STORAGE_KEY, JSON.stringify(values));
    setFeedback("Configurações salvas localmente às " + new Date().toLocaleTimeString("pt-BR"));
    showToast("Configurações salvas com sucesso.");
    return true;
}

function loadSettings() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
        writeValues(defaultValues());
        return;
    }

    try {
        const values = JSON.parse(stored);
        writeValues(values);
    } catch (error) {
        writeValues(defaultValues());
    }
}

function resetSettings() {
    const defaults = defaultValues();
    writeValues(defaults);
    localStorage.removeItem(STORAGE_KEY);
    setFeedback("Padrões restaurados.");
    showToast("Configurações restauradas.");
}

saveAllButton?.addEventListener("click", saveSettings);
resetButton?.addEventListener("click", resetSettings);

saveCardButtons.forEach((button) => {
    button.addEventListener("click", saveSettings);
});

settingFields.forEach((field) => {
    field.addEventListener("input", () => {
        setFeedback("Existem alterações não salvas.");
    });
    field.addEventListener("change", () => {
        setFeedback("Existem alterações não salvas.");
    });
});

loadSettings();
