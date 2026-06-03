const cidFilter = document.getElementById("cidFilter")
const monthFilter = document.getElementById("monthFilter")
const yearFilter = document.getElementById("yearFilter")
const generateButton = document.getElementById("generateReport")
const inssTableBody = document.getElementById("inssTableBody")

const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
const chartCtx = document.getElementById("reportChart")
let rankingChart

function parseISODate(isoDate) {
    const [year, month, day] = isoDate.split("-").map(Number)
    return new Date(year, month - 1, day)
}

function buildFilterOptions() {
    const cidSet = new Set()
    const yearSet = new Set()

    employees.forEach((employee) => {
        employee.saudeOcupacional.atestados.forEach((item) => {
            cidSet.add(item.cid)
            yearSet.add(parseISODate(item.data).getFullYear())
        })
    })

    Array.from(cidSet).sort().forEach((cid) => {
        const option = document.createElement("option")
        option.value = cid
        option.textContent = cid
        cidFilter.appendChild(option)
    })

    monthNames.forEach((name, index) => {
        const option = document.createElement("option")
        option.value = String(index + 1)
        option.textContent = name
        monthFilter.appendChild(option)
    })

    Array.from(yearSet).sort((a, b) => a - b).forEach((year) => {
        const option = document.createElement("option")
        option.value = String(year)
        option.textContent = String(year)
        yearFilter.appendChild(option)
    })
}

function matchesFilters(certificate, cid, month, year) {
    const date = parseISODate(certificate.data)
    const certificateMonth = date.getMonth() + 1
    const certificateYear = date.getFullYear()

    const cidMatch = !cid || certificate.cid === cid
    const monthMatch = !month || certificateMonth === Number(month)
    const yearMatch = !year || certificateYear === Number(year)

    return cidMatch && monthMatch && yearMatch
}

function getRanking(certificateFilter) {
    return employees
        .map((employee) => {
            const filteredCertificates = employee.saudeOcupacional.atestados.filter(certificateFilter)
            const totalDays = filteredCertificates.reduce((acc, item) => acc + item.dias, 0)

            return {
                nome: employee.nome,
                totalAtestados: filteredCertificates.length,
                diasAfastados: totalDays
            }
        })
        .filter((item) => item.totalAtestados > 0)
        .sort((a, b) => b.totalAtestados - a.totalAtestados)
}

function renderInssTable() {
    inssTableBody.innerHTML = ""

    const activeInss = employees.filter((employee) => employee.saudeOcupacional.afastamentoINSS.ativo)

    if (activeInss.length === 0) {
        const row = document.createElement("tr")
        row.innerHTML = "<td colspan='3'>Nenhum afastamento INSS ativo.</td>"
        inssTableBody.appendChild(row)
        return
    }

    activeInss.forEach((employee) => {
        const row = document.createElement("tr")
        row.innerHTML = `
            <td>${employee.nome}</td>
            <td>${employee.saudeOcupacional.afastamentoINSS.dataAfastamento}</td>
            <td>${employee.saudeOcupacional.afastamentoINSS.previsaoRetorno}</td>
        `
        inssTableBody.appendChild(row)
    })
}

function updateCards(ranking) {
    const totalCertificates = ranking.reduce((acc, item) => acc + item.totalAtestados, 0)
    const activeInss = employees.filter((employee) => employee.saudeOcupacional.afastamentoINSS.ativo).length
    const avgAbsenteeism = (
        employees.reduce((acc, employee) => acc + employee.saudeOcupacional.absenteismo.taxaMensal, 0) /
        employees.length
    ).toFixed(1)
    const accidentsTotal = employees.reduce((acc, employee) => acc + employee.saudeOcupacional.acidentes.quantidadeAno, 0)

    document.getElementById("totalCertificates").textContent = String(totalCertificates)
    document.getElementById("activeInss").textContent = String(activeInss)
    document.getElementById("avgAbsenteeism").textContent = `${avgAbsenteeism}%`
    document.getElementById("accidentsTotal").textContent = String(accidentsTotal)
}

function updateChart(ranking) {
    const labels = ranking.map((item) => item.nome)
    const values = ranking.map((item) => item.totalAtestados)

    if (rankingChart) {
        rankingChart.destroy()
    }

    rankingChart = new Chart(chartCtx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Qtd. de atestados",
                data: values,
                backgroundColor: "rgba(14, 165, 233, 0.75)",
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    })
}

function generateReport() {
    const selectedCID = cidFilter.value
    const selectedMonth = monthFilter.value
    const selectedYear = yearFilter.value

    const ranking = getRanking((certificate) => matchesFilters(certificate, selectedCID, selectedMonth, selectedYear))

    updateCards(ranking)
    updateChart(ranking)
    renderInssTable()
}

buildFilterOptions()
generateButton.addEventListener("click", generateReport)
generateReport()
