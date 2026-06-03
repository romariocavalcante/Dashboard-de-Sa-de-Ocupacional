function renderEmployeeOccupationalChart(canvasId, employee) {
    const target = document.getElementById(canvasId)

    if (!target || !employee) return null

    return new Chart(target, {
        type: "bar",
        data: {
            labels: ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            datasets: [{
                label: "Atestados no semestre",
                data: employee.graficos.atestadosAno,
                backgroundColor: "rgba(37, 99, 235, 0.75)",
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    })
}
