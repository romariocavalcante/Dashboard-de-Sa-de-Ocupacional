const tableBody = document.getElementById("employeeTable")
const searchInput = document.getElementById("searchInput")
const queryParams = new URLSearchParams(window.location.search)

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
        normalizeText(emp.cargo).includes(normalizedValue) ||
        normalizeText(emp.setor).includes(normalizedValue)
    )
}

function renderTable(data) {
    tableBody.innerHTML = ""

    data.forEach(emp => {
        const row = document.createElement("tr")
        const status = emp.saudeOcupacional.status
        const editButton = canEditEmployees
            ? `<button class="btn" onclick="editarFuncionario(${emp.id})">Editar</button>`
            : ""

        row.innerHTML = `
            <td>${emp.nome}</td>
            <td>${emp.cargo}</td>
            <td>${emp.setor}</td>
            <td class="status ${status}">
                ${status === "low" ? "Estável" :
                  status === "medium" ? "Atenção" : "Crítico"}
            </td>
            <td>
                <button class="btn btn-view" onclick="verFuncionario(${emp.id})">
                    Ver
                </button>
                ${editButton}
            </td>
        `

        tableBody.appendChild(row)
    })
}

function verFuncionario(id) {
    window.location.href = `/funcionarios/detalhes/?id=${id}`
}

function editarFuncionario(id) {
    window.location.href = `/funcionarios/${id}/editar/`
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
