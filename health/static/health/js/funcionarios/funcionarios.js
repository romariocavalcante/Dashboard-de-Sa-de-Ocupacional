const tableBody = document.getElementById("employeeTable")
const searchInput = document.getElementById("searchInput")
const queryParams = new URLSearchParams(window.location.search)
const cargoSelect = document.getElementById("cargoSelect")
const statusSelect = document.getElementById("statusSelect")

const OPTIONS_STORAGE_KEY = "health_employee_options_v1"
const DEFAULT_OPTIONS = {
    cargos: ["Operador", "Motorista", "Auxiliar", "Tecnico", "Analista"],
    status: [
        { value: "low", label: "Estavel" },
        { value: "medium", label: "Atencao" },
        { value: "high", label: "Critico" }
    ]
}

const ACCENT_FALLBACK_MAP = {
    "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
    "Á": "a", "À": "a", "Â": "a", "Ã": "a", "Ä": "a",
    "é": "e", "è": "e", "ê": "e", "ë": "e",
    "É": "e", "È": "e", "Ê": "e", "Ë": "e",
    "í": "i", "ì": "i", "î": "i", "ï": "i",
    "Í": "i", "Ì": "i", "Î": "i", "Ï": "i",
    "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
    "Ó": "o", "Ò": "o", "Ô": "o", "Õ": "o", "Ö": "o",
    "ú": "u", "ù": "u", "û": "u", "ü": "u",
    "Ú": "u", "Ù": "u", "Û": "u", "Ü": "u",
    "ç": "c", "Ç": "c",
    "ñ": "n", "Ñ": "n"
}

function stripAccents(value) {
    const text = String(value || "")

    if (typeof text.normalize === "function") {
        return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    }

    return text.replace(/[\u00C0-\u017F]/g, (char) => ACCENT_FALLBACK_MAP[char] || char)
}

function normalizeText(value) {
    return stripAccents(value)
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim()
}

function filterEmployees(value) {
    const normalizedValue = normalizeText(value)

    return employees.filter(emp =>
        normalizeText(emp.nome).includes(normalizedValue) ||
        normalizeText(emp.funcao).includes(normalizedValue)
    )
}

function renderTable(data) {
    tableBody.innerHTML = ""

    const statusLabelMap = buildStatusLabelMap()

    data.forEach(emp => {
        const row = document.createElement("tr")
        const status = emp.saudeOcupacional.status
        const removeButton = canEditEmployees
            ? `<button class="btn btn-danger" data-remove-id="${emp.id}">Remover</button>`
            : ""
        const editButton = canEditEmployees
            ? `<button class="btn" onclick="editarFuncionario(${emp.id})">Editar</button>`
            : ""

        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>${emp.funcao}</td>
            <td class="status ${statusClass(status)}">
                ${statusLabelMap.get(status) || status || "N/A"}
            </td>
            <td>
                <button class="btn btn-view" onclick="verFuncionario(${emp.id})">
                    Ver
                </button>
                ${editButton}
                ${removeButton}
            </td>
        `

        tableBody.appendChild(row)
    })

    if (canEditEmployees) {
        tableBody.querySelectorAll("[data-remove-id]").forEach((button) => {
            button.addEventListener("click", () => {
                const employeeId = button.dataset.removeId
                if (!employeeId) return
                const confirmed = window.confirm("Deseja remover este funcionario?")
                if (!confirmed) return

                fetch(`/funcionarios/${employeeId}/remover/`, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/json"
                    }
                }).then(() => window.location.reload())
            })
        })
    }
}

function statusClass(status) {
    if (status === "low" || status === "medium" || status === "high") {
        return status
    }

    return "custom"
}

function loadOptionLists() {
    const stored = localStorage.getItem(OPTIONS_STORAGE_KEY)
    if (!stored) return DEFAULT_OPTIONS

    try {
        const parsed = JSON.parse(stored)
        return {
            cargos: Array.isArray(parsed.cargos) ? parsed.cargos : DEFAULT_OPTIONS.cargos,
            status: Array.isArray(parsed.status) ? parsed.status : DEFAULT_OPTIONS.status
        }
    } catch (error) {
        return DEFAULT_OPTIONS
    }
}

function buildStatusLabelMap() {
    const options = loadOptionLists().status || []
    return new Map(options.map((option) => [option.value, option.label]))
}

function fillSelect(select, options, placeholder) {
    if (!select) return
    select.innerHTML = ""

    if (placeholder) {
        const placeholderOption = document.createElement("option")
        placeholderOption.value = ""
        placeholderOption.textContent = placeholder
        select.appendChild(placeholderOption)
    }

    options.forEach((option) => {
        const opt = document.createElement("option")
        if (typeof option === "string") {
            opt.value = option
            opt.textContent = option
        } else {
            opt.value = option.value
            opt.textContent = option.label
        }
        select.appendChild(opt)
    })
}

function verFuncionario(id) {
    window.location.href = `/funcionarios/detalhes/?id=${id}`
}

function editarFuncionario(id) {
    window.location.href = `/funcionarios/${id}/editar/`
}

function getCookie(name) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(";").shift()
    return ""
}

searchInput.addEventListener("input", () => {
    const value = searchInput.value

    renderTable(filterEmployees(value))
})

const initialSearch = queryParams.get("q")

if (initialSearch) {
    searchInput.value = initialSearch
    renderTable(filterEmployees(initialSearch))
} else {
    renderTable(employees)
}

const optionLists = loadOptionLists()
fillSelect(cargoSelect, optionLists.cargos, "Selecione a funcao")
fillSelect(statusSelect, optionLists.status, "Selecione o status")
