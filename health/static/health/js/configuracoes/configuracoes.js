const STORAGE_KEY = "health_settings_v1";
const OPTIONS_STORAGE_KEY = "health_employee_options_v1";

const settingFields = document.querySelectorAll("[data-setting]");
const saveAllButton = document.querySelector("#save-all-settings");
const resetButton = document.querySelector("#reset-settings");
const saveCardButtons = document.querySelectorAll(".btn-save-card");
const feedbackElement = document.querySelector("#save-feedback");
const toastElement = document.querySelector("#settings-toast");
const saveOptionsButton = document.querySelector(".btn-save-options");
const optionAddButtons = document.querySelectorAll("[data-add-option]");
const optionTabs = document.querySelectorAll("[data-option-tab]");
const optionPanels = document.querySelectorAll("[data-option-panel]");

const DEFAULT_OPTIONS = {
    cargos: ["Operador", "Motorista", "Auxiliar", "Tecnico", "Analista"],
    status: [
        { value: "low", label: "Estavel" },
        { value: "medium", label: "Atencao" },
        { value: "high", label: "Critico" }
    ]
};

const optionGroups = {
    cargos: {
        list: document.querySelector("#cargo-option-list"),
        input: document.querySelector("#cargo-option-input")
    },
    status: {
        list: document.querySelector("#status-option-list"),
        input: document.querySelector("#status-option-input")
    }
};

let optionState = structuredClone(DEFAULT_OPTIONS);

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
    saveOptionLists();
    setFeedback("Configurações salvas localmente às " + new Date().toLocaleTimeString("pt-BR"));
    showToast("Configurações salvas com sucesso.");
    return true;
}

function loadSettings() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
        writeValues(defaultValues());
        loadOptionLists();
        return;
    }

    try {
        const values = JSON.parse(stored);
        writeValues(values);
    } catch (error) {
        writeValues(defaultValues());
    }

    loadOptionLists();
}

function resetSettings() {
    const defaults = defaultValues();
    writeValues(defaults);
    localStorage.removeItem(STORAGE_KEY);
    optionState = structuredClone(DEFAULT_OPTIONS);
    localStorage.removeItem(OPTIONS_STORAGE_KEY);
    renderOptionLists();
    setFeedback("Padrões restaurados.");
    showToast("Configurações restauradas.");
}

function normalizeOptionText(value) {
    return String(value || "").trim();
}

function slugify(text) {
    return normalizeOptionText(text)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)+/g, "") || "status";
}

function loadOptionLists() {
    const stored = localStorage.getItem(OPTIONS_STORAGE_KEY);
    if (!stored) {
        optionState = structuredClone(DEFAULT_OPTIONS);
        renderOptionLists();
        return;
    }

    try {
        const parsed = JSON.parse(stored);
        optionState = {
            cargos: Array.isArray(parsed.cargos) ? parsed.cargos : DEFAULT_OPTIONS.cargos,
            status: Array.isArray(parsed.status) ? parsed.status : DEFAULT_OPTIONS.status
        };
    } catch (error) {
        optionState = structuredClone(DEFAULT_OPTIONS);
    }

    renderOptionLists();
}

function saveOptionLists() {
    localStorage.setItem(OPTIONS_STORAGE_KEY, JSON.stringify(optionState));
}

function renderOptionLists() {
    Object.entries(optionGroups).forEach(([key, group]) => {
        if (!group.list) return;
        group.list.innerHTML = "";

        const options = optionState[key] || [];
        options.forEach((option, index) => {
            const label = typeof option === "string" ? option : option.label;
            const value = typeof option === "string" ? "" : option.value;
            const item = document.createElement("div");
            item.className = "option-item";
            item.innerHTML = `
                <input type="text" data-option-group="${key}" data-option-index="${index}" value="${label}">
                ${value ? `<small>${value}</small>` : ""}
                <button type="button" data-remove-option="${key}" data-option-index="${index}">Remover</button>
            `;
            group.list.appendChild(item);
        });
    });
}

function syncOptionInput(groupKey, index, value) {
    const normalized = normalizeOptionText(value);
    if (!normalized) return;

    if (groupKey === "status") {
        const item = optionState.status[index];
        const valueKey = typeof item === "object" ? item.value : slugify(normalized);
        optionState.status[index] = { value: valueKey, label: normalized };
        return;
    }

    optionState[groupKey][index] = normalized;
}

function addOption(groupKey, value) {
    const normalized = normalizeOptionText(value);
    if (!normalized) return;

    if (groupKey === "status") {
        const valueKey = slugify(normalized);
        optionState.status.push({ value: valueKey, label: normalized });
    } else {
        optionState[groupKey].push(normalized);
    }

    renderOptionLists();
    saveOptionLists();
}

function removeOption(groupKey, index) {
    optionState[groupKey].splice(index, 1);
    renderOptionLists();
    saveOptionLists();
}

saveAllButton?.addEventListener("click", saveSettings);
resetButton?.addEventListener("click", resetSettings);
saveOptionsButton?.addEventListener("click", () => {
    saveOptionLists();
    setFeedback("Opções salvas localmente.");
    showToast("Opções salvas com sucesso.");
});

saveCardButtons.forEach((button) => {
    button.addEventListener("click", saveSettings);
});

optionTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const target = tab.dataset.optionTab;
        if (!target) return;
        optionTabs.forEach((button) => button.classList.toggle("is-active", button.dataset.optionTab === target));
        optionPanels.forEach((panel) => panel.classList.toggle("is-active", panel.dataset.optionPanel === target));
    });
});

optionAddButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const groupKey = button.dataset.addOption;
        const group = optionGroups[groupKey];
        if (!group || !group.input) return;
        addOption(groupKey, group.input.value);
        group.input.value = "";
    });
});

settingFields.forEach((field) => {
    field.addEventListener("input", () => {
        setFeedback("Existem alterações não salvas.");
    });
    field.addEventListener("change", () => {
        setFeedback("Existem alterações não salvas.");
    });
});

document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.dataset.optionGroup) return;
    const groupKey = target.dataset.optionGroup;
    const index = Number(target.dataset.optionIndex);
    if (!Number.isInteger(index)) return;
    syncOptionInput(groupKey, index, target.value);
    saveOptionLists();
});

document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    const groupKey = target.dataset.removeOption;
    if (!groupKey) return;
    const index = Number(target.dataset.optionIndex);
    if (!Number.isInteger(index)) return;
    removeOption(groupKey, index);
});

loadSettings();
