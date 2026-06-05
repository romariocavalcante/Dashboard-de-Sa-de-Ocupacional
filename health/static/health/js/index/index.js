const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const employeesList = Array.isArray(window.employees) ? window.employees : [];

function setTextIfExists(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = String(value);
}

function formatHours(totalHours) {
    const hours = Number(totalHours) || 0;
    return `${hours}`;
}

function parseISODate(isoDate) {
    if (!isoDate) return null;
    const [year, month, day] = String(isoDate).split("-").map(Number);
    if (!year || !month || !day) return null;
    return new Date(year, month - 1, day);
}

function addToMap(map, key, value) {
    if (!key) return;
    const numericValue = Number(value) || 0;
    map[key] = (map[key] || 0) + numericValue;
}

function buildMonthLabels(monthKeys) {
    return monthKeys.map((key) => {
        const parts = key.split("-");
        if (parts.length !== 2) return key;
        const monthIndex = Number(parts[1]) - 1;
        return `${monthNames[monthIndex] || parts[1]}/${parts[0]}`;
    });
}

function sortEntriesByValue(map, limit = null) {
    const entries = Object.entries(map || {}).sort((a, b) => b[1] - a[1]);
    return limit ? entries.slice(0, limit) : entries;
}

function computeAbsenteeismSummary(employees) {
    const summary = {
        totalAtestados: 0,
        totalDias: 0,
        totalHoras: 0,
        porMes: {},
        porCid: {},
        porMotivo: {},
        porArea: {},
        topFuncionarios: {}
    };

    employees.forEach((employee) => {
        const nome = employee?.nome || "";
        const unidade = employee?.unidade || "";
        const atestados = employee?.saudeOcupacional?.atestados || [];

        if (!Array.isArray(atestados) || atestados.length === 0) {
            return;
        }

        summary.topFuncionarios[nome] = (summary.topFuncionarios[nome] || 0) + atestados.length;

        atestados.forEach((atest) => {
            summary.totalAtestados += 1;
            const dias = Number(atest?.dias) || 0;
            summary.totalDias += dias;

            const date = parseISODate(atest?.data);
            if (date) {
                const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
                addToMap(summary.porMes, monthKey, dias);
            }

            addToMap(summary.porCid, atest?.cid || "Sem CID", 1);
            addToMap(summary.porMotivo, atest?.motivo || "Sem motivo", 1);
            addToMap(summary.porArea, atest?.area || unidade || "Sem area", 1);
        });
    });

    summary.totalHoras = summary.totalDias * 8;
    summary.topFuncionarios = Object.fromEntries(sortEntriesByValue(summary.topFuncionarios, 10));
    summary.porCid = Object.fromEntries(sortEntriesByValue(summary.porCid, 10));
    summary.porMotivo = Object.fromEntries(sortEntriesByValue(summary.porMotivo, 10));
    summary.porArea = Object.fromEntries(sortEntriesByValue(summary.porArea, 10));

    return summary;
}

function buildChart(ctx, config) {
    if (!ctx || typeof Chart === "undefined") return null;
    return new Chart(ctx, config);
}

const absenteeismData = computeAbsenteeismSummary(employeesList);
const totalAtestados = absenteeismData.totalAtestados ?? 0;
const totalDias = absenteeismData.totalDias ?? 0;
const totalHoras = absenteeismData.totalHoras ?? 0;

setTextIfExists("totalAtestados", totalAtestados);
setTextIfExists("totalDias", totalDias);
setTextIfExists("totalHoras", formatHours(totalHoras));

const totalAsos = employeesList.length;
const asosNoPrazo = employeesList.filter((employee) => employee?.saudeOcupacional?.exames?.status === "em_dia").length;
const asosProximos = employeesList.filter((employee) => {
    const status = employee?.saudeOcupacional?.exames?.status;
    return status === "vence60" || status === "vence90";
}).length;
const asosPercent = totalAsos ? Math.round((asosNoPrazo / totalAsos) * 100) : 0;

setTextIfExists("asosTotal", totalAsos);
setTextIfExists("asosProximos", asosProximos);
setTextIfExists("asosNoPrazo", asosNoPrazo);
setTextIfExists("asosPercent", `${asosPercent}%`);

const monthKeys = Object.keys(absenteeismData.porMes || {}).sort();
const monthLabels = buildMonthLabels(monthKeys);
const monthValues = monthKeys.map((key) => absenteeismData.porMes[key]);

buildChart(document.getElementById("atestadosMesChart"), {
    type: "line",
    data: {
        labels: monthLabels,
        datasets: [{
            label: "Dias afastados",
            data: monthValues,
            borderColor: "#1c4b8f",
            backgroundColor: "rgba(28, 75, 143, 0.2)",
            tension: 0.35,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: "#1c4b8f"
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
                beginAtZero: true
            }
        }
    }
});

buildChart(document.getElementById("atestadosTipoChart"), {
    type: "doughnut",
    data: {
        labels: Object.keys(absenteeismData.porMotivo || {}),
        datasets: [{
            data: Object.values(absenteeismData.porMotivo || {}),
            backgroundColor: ["#0b4b8f", "#4f8fd6", "#a4c7ee", "#1e88e5", "#90caf9"]
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: "bottom"
            }
        }
    }
});

buildChart(document.getElementById("atestadosAreaChart"), {
    type: "bar",
    data: {
        labels: Object.keys(absenteeismData.porArea || {}),
        datasets: [{
            label: "Atestados",
            data: Object.values(absenteeismData.porArea || {}),
            backgroundColor: "rgba(15, 118, 110, 0.75)",
            borderRadius: 10
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
                beginAtZero: true
            }
        }
    }
});

buildChart(document.getElementById("atestadosCidChart"), {
    type: "bar",
    data: {
        labels: Object.keys(absenteeismData.porCid || {}),
        datasets: [{
            label: "Ocorrencias",
            data: Object.values(absenteeismData.porCid || {}),
            backgroundColor: "rgba(22, 78, 99, 0.75)",
            borderRadius: 10
        }]
    },
    options: {
        indexAxis: "y",
        responsive: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: {
            x: {
                beginAtZero: true
            }
        }
    }
});

buildChart(document.getElementById("topFuncionariosChart"), {
    type: "bar",
    data: {
        labels: Object.keys(absenteeismData.topFuncionarios || {}),
        datasets: [{
            label: "Atestados",
            data: Object.values(absenteeismData.topFuncionarios || {}),
            backgroundColor: "rgba(30, 64, 175, 0.8)",
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
});

