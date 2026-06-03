const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const today = new Date();
const currentMonth = today.getMonth() + 1;
const currentYear = today.getFullYear();
const moduleTabs = document.querySelectorAll("[data-module-target]");
const modulePanels = document.querySelectorAll("[data-module-panel]");

function activateModule(moduleKey) {
    moduleTabs.forEach((tab) => {
        tab.classList.toggle("is-active", tab.dataset.moduleTarget === moduleKey);
    });

    modulePanels.forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.modulePanel === moduleKey);
    });
}

moduleTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const moduleKey = tab.dataset.moduleTarget;
        if (!moduleKey) return;

        activateModule(moduleKey);
    });
});

function setTextIfExists(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = String(value);
}

function parseISODate(isoDate) {
    if (!isoDate) return null;

    const [year, month, day] = isoDate.split("-").map(Number);
    return new Date(year, month - 1, day);
}

function countCertificatesByMonthAndYear(employee, month, year) {
    return employee.saudeOcupacional.atestados.filter((item) => {
        const date = parseISODate(item.data);
        return date && (date.getMonth() + 1) === month && date.getFullYear() === year;
    }).length;
}

function aggregateCertificatesPerMonth(year) {
    const monthlyTotals = Array(12).fill(0);

    employees.forEach((employee) => {
        employee.saudeOcupacional.atestados.forEach((item) => {
            const date = parseISODate(item.data);

            if (date && date.getFullYear() === year) {
                monthlyTotals[date.getMonth()] += 1;
            }
        });
    });

    return monthlyTotals;
}

function aggregateAccidentsByType() {
    const byType = {};

    employees.forEach((employee) => {
        const accidentType = employee.saudeOcupacional.acidentes.ultimoTipo;

        if (accidentType && accidentType !== "Sem registro") {
            byType[accidentType] = (byType[accidentType] || 0) + 1;
        }
    });

    return byType;
}

const inssActive = dashboardStats?.inss_active ?? 0;
const expiredExams = dashboardStats?.expired_exams ?? 0;
const exams60 = dashboardStats?.exams_60 ?? 0;
const exams90 = dashboardStats?.exams_90 ?? 0;
const totalMonthCertificates = dashboardStats?.month_certificates ?? 0;
const averageAbsenteeism = dashboardStats?.absenteeism_rate ?? 0;
const topEmployee = dashboardStats?.top_employee;

setTextIfExists("monthCertificates", totalMonthCertificates);
setTextIfExists("inssActive", inssActive);
setTextIfExists("expiredExams", expiredExams);
setTextIfExists("absenteeismRate", `${averageAbsenteeism.toFixed ? averageAbsenteeism.toFixed(1) : averageAbsenteeism}%`);
setTextIfExists("exams60", exams60);
setTextIfExists("exams90", exams90);
setTextIfExists("topEmployee", topEmployee && topEmployee.total > 0 ? `${topEmployee.nome} (${topEmployee.total})` : "-");

const alertElement = document.getElementById("alert");

if (alertElement && dashboardStats?.alert_text) {
    alertElement.textContent = dashboardStats.alert_text;
}

const certificatesChartCtx = document.getElementById("certificatesChart");
const certificatesSeries = dashboardStats?.certificates_series ?? aggregateCertificatesPerMonth(currentYear);

if (certificatesChartCtx) {
    new Chart(certificatesChartCtx, {
        type: "bar",
        data: {
            labels: monthNames,
            datasets: [{
                label: "Atestados",
                data: certificatesSeries,
                backgroundColor: "rgba(37, 99, 235, 0.7)",
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
}

const accidentsChartCtx = document.getElementById("accidentsChart");
const accidentsByType = dashboardStats?.accidents_by_type ?? aggregateAccidentsByType();
const accidentLabels = Object.keys(accidentsByType);
const accidentValues = Object.values(accidentsByType);

if (accidentsChartCtx) {
    new Chart(accidentsChartCtx, {
        type: "doughnut",
        data: {
            labels: accidentLabels,
            datasets: [{
                data: accidentValues,
                backgroundColor: [
                    "#0ea5e9",
                    "#f59e0b",
                    "#ef4444",
                    "#14b8a6",
                    "#8b5cf6"
                ]
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
}

