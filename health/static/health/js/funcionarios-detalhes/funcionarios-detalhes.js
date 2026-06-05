const params = new URLSearchParams(window.location.search)
const id = Number(params.get("id"))

const emp = employees.find(e => e.id === id)

if (!emp) {
    window.location.href = "/funcionarios/"
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

function displayValue(value, fallback = "-") {
    if (value === null || value === undefined) return fallback
    const text = String(value).trim()
    return text ? text : fallback
}

function renderAtestadosList(atestados) {
    if (!Array.isArray(atestados) || atestados.length === 0) {
        return "<p class=\"subtitle\">Sem atestados registrados.</p>"
    }

    const rows = atestados.map((atestado) => {
        return `
            <tr>
                <td>${displayValue(atestado.data)}</td>
                <td>${displayValue(atestado.cid)}</td>
                <td>${displayValue(atestado.dias, "0")}</td>
                <td>${displayValue(atestado.motivo)}</td>
                <td>${displayValue(atestado.area)}</td>
            </tr>
        `
    }).join("")

    return `
        <table class="employee-table">
            <thead>
                <tr>
                    <th>Data</th>
                    <th>CID</th>
                    <th>Dias</th>
                    <th>Motivo</th>
                    <th>Area</th>
                </tr>
            </thead>
            <tbody>
                ${rows}
            </tbody>
        </table>
    `
}

content.innerHTML = `
    <header class="page-header">
        <h2>${emp.nome}</h2>
        <span>${emp.funcao}</span>
    </header>

    ${canEditEmployees ? `<div class="top-bar"><a class="btn btn-view" href="/funcionarios/${emp.id}/editar/">Editar funcionário</a></div>` : ""}

    <section class="chart-card">
        <h3>Dados do funcionario</h3>
        <div class="employee-details">
            <div class="detail-row"><span>Chapa</span><strong>${displayValue(emp.chapa)}</strong></div>
            <div class="detail-row"><span>Nome</span><strong>${displayValue(emp.nome)}</strong></div>
            <div class="detail-row"><span>Funcao</span><strong>${displayValue(emp.funcao)}</strong></div>
            <div class="detail-row"><span>Secao</span><strong>${displayValue(emp.secao)}</strong></div>
            <div class="detail-row"><span>Dt inicio</span><strong>${displayValue(emp.dt_inicio)}</strong></div>
            <div class="detail-row"><span>Dt final</span><strong>${displayValue(emp.dt_final)}</strong></div>
            <div class="detail-row"><span>Dias afastados</span><strong>${displayValue(emp.dias_afastados, "0")}</strong></div>
            <div class="detail-row"><span>Motivo</span><strong>${displayValue(emp.motivo)}</strong></div>
            <div class="detail-row"><span>CID</span><strong>${displayValue(emp.cid)}</strong></div>
            <div class="detail-row"><span>Qtd atestados</span><strong>${displayValue(emp.qtd_atestados, "0")}</strong></div>
        </div>
    </section>

    <div class="employee-metrics">
        <div class="metric-pill">
            <span>Status</span>
            <strong class="status ${emp.saudeOcupacional.status}">
                ${emp.saudeOcupacional.status === "low" ? "Estável" :
                  emp.saudeOcupacional.status === "medium" ? "Atenção" : "Crítico"}
            </strong>
        </div>
        <div class="metric-pill">
            <span>Atestados (ano)</span>
            <strong>${emp.saudeOcupacional.atestados.length}</strong>
        </div>
        <div class="metric-pill">
            <span>Absenteísmo mensal</span>
            <strong>${emp.saudeOcupacional.absenteismo.taxaMensal.toFixed(1)}%</strong>
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
        <div class="chart-compact">
            <canvas id="employeeCertificatesChart"></canvas>
        </div>
    </div>

    <div class="chart-card">
        <h3>Atestados detalhados</h3>
        ${renderAtestadosList(emp.saudeOcupacional.atestados)}
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
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false
            }
        },
        layout: {
            padding: {
                top: 4,
                bottom: 4
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