const params = new URLSearchParams(window.location.search)
const id = Number(params.get("id"))

const emp = employees.find(e => e.id === id)

if (!emp) {
    window.location.href = "funcionarios.html"
}

const content = document.getElementById("content")
const monthLabels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

function parseISODate(isoDate) {
    if (!isoDate) return null

    const [year, month, day] = isoDate.split("-").map(Number)
    return new Date(year, month - 1, day)
}

function normalizeExamStatus(status) {
    const labels = {
        vencido: "Vencido",
        vence60: "Vence em 60 dias",
        vence90: "Vence em 90 dias",
        em_dia: "Em dia"
    }

    return labels[status] || "Não informado"
}

content.innerHTML = `
    <header class="page-header">
        <h2>${emp.nome}</h2>
        <span>${emp.cargo}</span>
    </header>

    ${canEditEmployees ? `<div class="top-bar"><a class="btn btn-view" href="/funcionarios/${emp.id}/editar/">Editar funcionário</a></div>` : ""}

    <div class="employee-summary">
        <div class="summary-card">
            <h4>Setor</h4>
            <p>${emp.setor}</p>
        </div>

        <div class="summary-card">
            <h4>Status Ocupacional</h4>
            <p class="status ${emp.saudeOcupacional.status}">
                ${emp.saudeOcupacional.status === "low" ? "Estável" :
                  emp.saudeOcupacional.status === "medium" ? "Atenção" : "Crítico"}
            </p>
        </div>

        <div class="summary-card">
            <h4>Total de Atestados (ano)</h4>
            <p>${emp.saudeOcupacional.atestados.length}</p>
        </div>

        <div class="summary-card">
            <h4>Absenteísmo Mensal</h4>
            <p>${emp.saudeOcupacional.absenteismo.taxaMensal.toFixed(1)}%</p>
        </div>
    </div>

    <div class="indicators">
        <div class="indicator">
            <h4>INSS</h4>
            <p>
                ${emp.saudeOcupacional.afastamentoINSS.ativo
                    ? `Afastado desde ${emp.saudeOcupacional.afastamentoINSS.dataAfastamento} (retorno ${emp.saudeOcupacional.afastamentoINSS.previsaoRetorno})`
                    : "Sem afastamento ativo"}
            </p>
        </div>

        <div class="indicator">
            <h4>Exame Periódico</h4>
            <p>
                ${normalizeExamStatus(emp.saudeOcupacional.exames.status)}
                (${emp.saudeOcupacional.exames.proximoPeriodico})
            </p>
        </div>

        <div class="indicator risk">
            <h4>Acidentes no Ano</h4>
            <p>${emp.saudeOcupacional.acidentes.quantidadeAno}</p>
        </div>
    </div>

    <div class="chart-card">
        <h3>Atestados por mês</h3>
        <canvas id="employeeCertificatesChart"></canvas>
    </div>
`

const employeeCertificates = Array(12).fill(0)

emp.saudeOcupacional.atestados.forEach((item) => {
    const date = parseISODate(item.data)

    if (date) {
        employeeCertificates[date.getMonth()] += 1
    }
})

const certificatesCtx = document.getElementById("employeeCertificatesChart")

new Chart(certificatesCtx, {
    type: "bar",
    data: {
        labels: monthLabels,
        datasets: [{
            label: "Atestados",
            data: employeeCertificates,
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