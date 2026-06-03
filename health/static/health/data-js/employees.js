const employees = [
    {
        id: 1,
        nome: "João Silva",
        cargo: "Operador de Máquina",
        setor: "Produção",
        saudeOcupacional: {
            status: "low",
            atestados: [
                { data: "2026-01-12", cid: "M54", dias: 2 },
                { data: "2026-03-05", cid: "J11", dias: 1 },
                { data: "2026-05-18", cid: "S93", dias: 4 }
            ],
            afastamentoINSS: {
                ativo: false,
                dataAfastamento: null,
                previsaoRetorno: null
            },
            exames: {
                status: "vence90",
                proximoPeriodico: "2026-08-25",
                realizadoNoMes: false
            },
            acidentes: {
                quantidadeAno: 1,
                ultimoTipo: "Corte leve",
                dataUltimo: "2026-02-10"
            },
            absenteismo: {
                taxaMensal: 2.4,
                horasPerdidasMes: 9
            }
        },
        graficos: {
            atestadosAno: [1, 0, 1, 0, 1, 0],
            absenteismoSemestre: [2.1, 2.2, 2.0, 2.4, 2.3, 2.4]
        }
    },
    {
        id: 2,
        nome: "Maria Santos",
        cargo: "Analista de TI",
        setor: "Tecnologia",
        saudeOcupacional: {
            status: "medium",
            atestados: [
                { data: "2026-01-21", cid: "F41", dias: 3 },
                { data: "2026-04-02", cid: "J11", dias: 2 },
                { data: "2026-05-27", cid: "M79", dias: 1 },
                { data: "2026-05-30", cid: "M79", dias: 1 }
            ],
            afastamentoINSS: {
                ativo: true,
                dataAfastamento: "2026-05-20",
                previsaoRetorno: "2026-07-15"
            },
            exames: {
                status: "vence60",
                proximoPeriodico: "2026-07-22",
                realizadoNoMes: true
            },
            acidentes: {
                quantidadeAno: 0,
                ultimoTipo: "Sem registro",
                dataUltimo: null
            },
            absenteismo: {
                taxaMensal: 4.8,
                horasPerdidasMes: 18
            }
        },
        graficos: {
            atestadosAno: [1, 0, 0, 1, 2, 0],
            absenteismoSemestre: [3.9, 4.1, 4.4, 4.6, 4.7, 4.8]
        }
    },
    {
        id: 3,
        nome: "Carlos Pereira",
        cargo: "Supervisor",
        setor: "Operações",
        saudeOcupacional: {
            status: "high",
            atestados: [
                { data: "2026-02-11", cid: "I10", dias: 2 },
                { data: "2026-03-19", cid: "I10", dias: 1 },
                { data: "2026-05-06", cid: "M54", dias: 3 },
                { data: "2026-05-21", cid: "M54", dias: 2 },
                { data: "2026-05-29", cid: "S93", dias: 4 }
            ],
            afastamentoINSS: {
                ativo: true,
                dataAfastamento: "2026-04-28",
                previsaoRetorno: "2026-06-30"
            },
            exames: {
                status: "vencido",
                proximoPeriodico: "2026-04-10",
                realizadoNoMes: false
            },
            acidentes: {
                quantidadeAno: 2,
                ultimoTipo: "Entorse",
                dataUltimo: "2026-05-14"
            },
            absenteismo: {
                taxaMensal: 6.2,
                horasPerdidasMes: 24
            }
        },
        graficos: {
            atestadosAno: [0, 1, 1, 0, 3, 0],
            absenteismoSemestre: [4.8, 5.2, 5.6, 5.9, 6.0, 6.2]
        }
    },
    {
        id: 4,
        nome: "Ana Costa",
        cargo: "Técnica de Enfermagem",
        setor: "Ambulatório",
        saudeOcupacional: {
            status: "low",
            atestados: [
                { data: "2026-01-08", cid: "J11", dias: 1 },
                { data: "2026-05-03", cid: "G43", dias: 1 }
            ],
            afastamentoINSS: {
                ativo: false,
                dataAfastamento: null,
                previsaoRetorno: null
            },
            exames: {
                status: "em_dia",
                proximoPeriodico: "2026-10-19",
                realizadoNoMes: true
            },
            acidentes: {
                quantidadeAno: 0,
                ultimoTipo: "Sem registro",
                dataUltimo: null
            },
            absenteismo: {
                taxaMensal: 1.7,
                horasPerdidasMes: 7
            }
        },
        graficos: {
            atestadosAno: [1, 0, 0, 0, 1, 0],
            absenteismoSemestre: [1.5, 1.6, 1.5, 1.7, 1.8, 1.7]
        }
    }
]
