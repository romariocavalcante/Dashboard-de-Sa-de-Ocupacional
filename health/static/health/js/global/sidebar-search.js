const sidebarSearchBox = document.querySelector(".sidebar .search")

if (sidebarSearchBox) {
    const sidebarInput = sidebarSearchBox.querySelector("input")
    const sidebarButton = sidebarSearchBox.querySelector("button")

    const runSearch = () => {
        const query = sidebarInput.value.trim()
        const url = new URL("/funcionarios/", window.location.origin)

        if (query) {
            url.searchParams.set("q", query)
        }

        window.location.href = url.toString()
    }

    sidebarButton.addEventListener("click", runSearch)

    sidebarInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault()
            runSearch()
        }
    })
}
