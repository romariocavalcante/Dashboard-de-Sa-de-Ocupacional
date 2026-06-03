const container = document.getElementById("dashboardContainer")
const modeButtons = document.querySelectorAll("[data-view-mode]")
const visibilityManager = document.getElementById("cardVisibilityManager")
const visibilityButtons = document.querySelectorAll("[data-toggle-item-id]")
const dashboardCardButtons = document.querySelectorAll("[data-toggle-dashboard-card-key]")

let currentMode = container.classList.contains("grid") ? "grid" : "cards"

function getCookie(name) {
    const value = `; ${document.cookie}`
    const parts = value.split(`; ${name}=`)
    if (parts.length === 2) return parts.pop().split(";").shift()
    return ""
}

function saveLayout() {
    const order = [...container.querySelectorAll(".item-card")].map((node) => Number(node.dataset.itemId))
    const hiddenIds = [...container.querySelectorAll(".item-card.user-hidden")].map((node) => Number(node.dataset.itemId))
    const hiddenDashboardCards = [...dashboardCardButtons]
        .filter((button) => button.classList.contains("is-hidden-card"))
        .map((button) => button.dataset.toggleDashboardCardKey)

    fetch("/painel/layout/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            order,
            view_mode: currentMode,
            hidden_ids: hiddenIds,
            hidden_dashboard_cards: hiddenDashboardCards
        })
    })
}

function updateButtonLabel(button, hidden, hiddenLabel, visibleLabel) {
    const labelParts = button.textContent.split(" - ")
    const itemTitle = labelParts.slice(1).join(" - ")
    button.textContent = `${hidden ? hiddenLabel : visibleLabel} - ${itemTitle}`
}

function updateModeUI() {
    container.classList.remove("cards", "grid")
    container.classList.add(currentMode)

    modeButtons.forEach((button) => {
        button.classList.remove("btn-view")
        if (button.dataset.viewMode === currentMode) {
            button.classList.add("btn-view")
        }
    })

    const isCards = currentMode === "cards"

    if (visibilityManager) {
        visibilityManager.classList.toggle("is-hidden", !isCards)
    }

    container.querySelectorAll(".item-card").forEach((card) => {
        card.classList.toggle("is-hidden", card.classList.contains("user-hidden"))
    })
}

function toggleCardVisibility(itemId) {
    const card = container.querySelector(`.item-card[data-item-id='${itemId}']`)
    const button = document.querySelector(`[data-toggle-item-id='${itemId}']`)

    if (!card || !button) return

    card.classList.toggle("user-hidden")
    const hidden = card.classList.contains("user-hidden")

    button.classList.toggle("is-hidden-card", hidden)
    updateButtonLabel(button, hidden, "Adicionar", "Remover")

    updateModeUI()
    saveLayout()
}

function toggleDashboardCardVisibility(cardKey) {
    const button = document.querySelector(`[data-toggle-dashboard-card-key='${cardKey}']`)

    if (!button) return

    const hidden = button.classList.toggle("is-hidden-card")
    updateButtonLabel(button, hidden, "Adicionar", "Remover")

    saveLayout()
}

new Sortable(container, {
    animation: 150,
    onEnd: saveLayout
})

modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const mode = button.dataset.viewMode
        if (!mode) return

        currentMode = mode
        updateModeUI()
        saveLayout()
    })
})

visibilityButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const itemId = button.dataset.toggleItemId
        if (!itemId) return

        toggleCardVisibility(itemId)
    })
})

dashboardCardButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const cardKey = button.dataset.toggleDashboardCardKey
        if (!cardKey) return

        toggleDashboardCardVisibility(cardKey)
    })
})

updateModeUI()
