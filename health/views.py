import json
from datetime import datetime
from collections import Counter, defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import DashboardEntry, DashboardField, DashboardItem, DashboardModuleSetting, EmployeeRecord, UserDashboardLayout


SUMMARY_DASHBOARD_CARDS = [
	{"key": "month_certificates", "title": "Atestados Cadastrados", "element_id": "monthCertificates"},
	{"key": "inss_active", "title": "Afastados INSS", "element_id": "inssActive"},
	{"key": "expired_exams", "title": "Exames Vencidos", "element_id": "expiredExams"},
	{"key": "alert", "title": "Alerta", "element_id": "alert"},
	{"key": "certificates_chart", "title": "Atestados por Mês (Ano Atual)", "element_id": "certificatesChart"},
	{"key": "accidents_chart", "title": "Acidentes por Tipo", "element_id": "accidentsChart"},
	{"key": "absenteeism_rate", "title": "Absenteísmo Médio", "element_id": "absenteeismRate"},
	{"key": "exams_60", "title": "Exames vencem em 60 dias", "element_id": "exams60"},
	{"key": "exams_90", "title": "Exames vencem em 90 dias", "element_id": "exams90"},
	{"key": "top_employee", "title": "Top colaborador em atestados", "element_id": "topEmployee"},
]

SUMMARY_DASHBOARD_CARD_KEYS = {card["key"] for card in SUMMARY_DASHBOARD_CARDS}
STANDARD_MONTHLY_WORK_HOURS = 176

MODULE_REGISTRY = [
	("executive", "Visão Executiva (KPIs)", "Indicadores críticos para acompanhamento da diretoria."),
	("exams", "Exames Ocupacionais", "Status dos exames e conformidade legal dos colaboradores."),
	("leave_inss", "Afastamentos e INSS", "Visão de impacto operacional e evolução de afastamentos."),
	("accidents", "Acidentes e CAT", "Monitoramento de segurança, gravidade e registro de acidentes."),
	("absenteeism_health", "Absenteísmo e Saúde dos Colaboradores", "Saúde ocupacional ampliada, absenteísmo e alertas preventivos."),
]


def calculate_absenteeism_from_atestados(atestados):
	today = datetime.today()
	month = today.month
	year = today.year
	perdidos_dias_mes = 0

	for atestado in atestados:
		date = _parse_iso_date(atestado.get("data"))
		if not date or date.month != month or date.year != year:
			continue

		perdidos_dias_mes += max(_to_number(atestado.get("dias"), int, 0), 0)

	horas_perdidas_mes = perdidos_dias_mes * 8
	taxa_mensal = round((horas_perdidas_mes / STANDARD_MONTHLY_WORK_HOURS) * 100, 1) if STANDARD_MONTHLY_WORK_HOURS else 0.0

	return {
		"taxaMensal": taxa_mensal,
		"horasPerdidasMes": horas_perdidas_mes,
	}


def normalize_employee_payload(employee_payload):
	payload = dict(employee_payload or {})
	saude = dict(payload.get("saudeOcupacional") or {})
	atestados = list(saude.get("atestados") or [])
	saude["absenteismo"] = calculate_absenteeism_from_atestados(atestados)
	payload["saudeOcupacional"] = saude
	return payload


def get_active_employee_payloads():
	raw_payloads = EmployeeRecord.objects.filter(ativo=True).values_list("payload", flat=True)
	return [normalize_employee_payload(payload) for payload in raw_payloads]


def _parse_iso_date(value):
	if not value:
		return None

	try:
		return datetime.strptime(str(value), "%Y-%m-%d")
	except ValueError:
		return None


def build_dashboard_stats(employee_payloads):
	today = datetime.today()
	current_month = today.month
	current_year = today.year

	inss_active = 0
	expired_exams = 0
	exams60 = 0
	exams90 = 0
	total_certificates = 0
	total_absenteeism = 0.0
	month_certificates_series = [0] * 12
	accidents_by_type = {}
	top_employee = {"nome": "-", "total": 0}

	for employee in employee_payloads:
		saude = employee.get("saudeOcupacional", {}) or {}
		atestados = saude.get("atestados", []) or []
		afastamento = saude.get("afastamentoINSS", {}) or {}
		exames = saude.get("exames", {}) or {}
		acidentes = saude.get("acidentes", {}) or {}
		absenteismo = saude.get("absenteismo", {}) or {}

		if afastamento.get("ativo"):
			inss_active += 1

		status = exames.get("status")
		if status == "vencido":
			expired_exams += 1
		elif status == "vence60":
			exams60 += 1
		elif status == "vence90":
			exams90 += 1

		for atestado in atestados:
			date = _parse_iso_date(atestado.get("data"))
			total_certificates += 1
			if not date:
				continue

			if date.year == current_year:
				month_certificates_series[date.month - 1] += 1

		accident_type = acidentes.get("ultimoTipo")
		if accident_type and accident_type != "Sem registro":
			accidents_by_type[accident_type] = accidents_by_type.get(accident_type, 0) + 1

		total_absenteeism += float(absenteismo.get("taxaMensal") or 0)

		if len(atestados) > top_employee["total"]:
			top_employee = {"nome": employee.get("nome", "-"), "total": len(atestados)}

	average_absenteeism = round(total_absenteeism / len(employee_payloads), 1) if employee_payloads else 0.0

	if expired_exams > 0 and inss_active > 0:
		alert_text = "Atenção: há exames vencidos e colaboradores afastados pelo INSS ativos."
	elif expired_exams > 0:
		alert_text = "Atenção: existem exames periódicos vencidos aguardando regularização."
	elif inss_active > 0:
		alert_text = "Monitorar datas de retorno dos afastamentos INSS em andamento."
	else:
		alert_text = "Sem alertas críticos hoje."

	return {
		"month_certificates": total_certificates,
		"inss_active": inss_active,
		"expired_exams": expired_exams,
		"exams60": exams60,
		"exams90": exams90,
		"absenteeism_rate": average_absenteeism,
		"top_employee": top_employee,
		"alert_text": alert_text,
		"certificates_series": month_certificates_series,
		"accidents_by_type": accidents_by_type,
	}


def ensure_default_module_settings():
	for index, (module_key, _label, _description) in enumerate(MODULE_REGISTRY):
		DashboardModuleSetting.objects.get_or_create(
			module_key=module_key,
			defaults={"order": index, "enabled": True},
		)


def _to_number(value, number_type=float, default=0):
	try:
		return number_type(value)
	except (TypeError, ValueError):
		return default


def _format_percent(value):
	return f"{value:.1f}%"


def _format_top_counter(counter_obj, limit=5):
	if not counter_obj:
		return "Sem dados"

	return ", ".join([f"{label} ({count})" for label, count in counter_obj.most_common(limit)])


def _counter_rows(counter_obj, key_label, value_label, limit=10):
	if not counter_obj:
		return []

	return [
		{key_label: label, value_label: count}
		for label, count in counter_obj.most_common(limit)
	]


def _table_metric(label, rows, headers, keys, empty_message="Sem dados"):
	return {
		"label": label,
		"value": empty_message,
		"table_rows": rows,
		"table_headers": headers,
		"table_keys": keys,
	}


def _table_metric_from_counter(label, counter_obj, key_label, value_label, headers, keys, limit=10):
	rows = _counter_rows(counter_obj, key_label, value_label, limit)
	return _table_metric(label, rows, headers, keys)


def _build_dashboard_facts(employee_payloads, dashboard_stats):
	total_colaboradores = len(employee_payloads)

	status_counter = Counter()
	cid_counter = Counter()
	afastamentos_setor = Counter()
	afastamentos_unidade = Counter()
	afastamentos_por_colaborador = Counter()
	acidentes_setor = Counter()
	acidentes_tipo = Counter()
	absenteismo_setor = defaultdict(list)
	horas_perdidas_total = 0
	dias_perdidos_total = 0
	mental_health_cids = Counter()
	mental_health_away = 0
	restricoes_medicas = 0
	aptos = 0
	inaptos = 0
	total_exames = 0

	for employee in employee_payloads:
		nome = employee.get("nome", "Colaborador")
		setor = employee.get("setor") or "Sem setor"
		unidade = employee.get("unidade") or "Sem unidade"
		saude = employee.get("saudeOcupacional", {}) or {}
		afastamento = saude.get("afastamentoINSS", {}) or {}
		exames = saude.get("exames", {}) or {}
		acidentes = saude.get("acidentes", {}) or {}
		absenteismo = saude.get("absenteismo", {}) or {}
		atestados = saude.get("atestados", []) or []

		exame_status = exames.get("status") or "nao_informado"
		status_counter[exame_status] += 1
		total_exames += 1

		if exame_status == "vencido":
			inaptos += 1
		else:
			aptos += 1

		if saude.get("status") in {"medium", "high"}:
			restricoes_medicas += 1

		if afastamento.get("ativo"):
			afastamentos_setor[setor] += 1
			afastamentos_unidade[unidade] += 1
			afastamentos_por_colaborador[nome] += 1

		acidentes_quantidade = _to_number(acidentes.get("quantidadeAno"), int, 0)
		if acidentes_quantidade > 0:
			acidentes_setor[setor] += acidentes_quantidade
			acidentes_tipo[acidentes.get("ultimoTipo") or "Não informado"] += acidentes_quantidade

		taxa_mensal = _to_number(absenteismo.get("taxaMensal"), float, 0.0)
		horas_perdidas = _to_number(absenteismo.get("horasPerdidasMes"), float, 0.0)
		absenteismo_setor[setor].append(taxa_mensal)
		horas_perdidas_total += horas_perdidas

		for atestado in atestados:
			cid = (atestado.get("cid") or "Não informado").strip()
			dias = _to_number(atestado.get("dias"), int, 0)
			dias_perdidos_total += max(dias, 0)
			cid_counter[cid] += 1

			if cid.upper().startswith("F"):
				mental_health_cids[cid] += 1
				if afastamento.get("ativo"):
					mental_health_away += 1

	absenteismo_setor_text = {
		setor: _format_percent(sum(values) / len(values)) if values else "0.0%"
		for setor, values in absenteismo_setor.items()
	}

	acidentes_total = sum(acidentes_setor.values())
	taxa_frequencia = (acidentes_total / total_colaboradores * 100) if total_colaboradores else 0.0
	taxa_gravidade = (dias_perdidos_total / acidentes_total) if acidentes_total else 0.0

	avg_tempo_afastamento = (dias_perdidos_total / dashboard_stats["month_certificates"]) if dashboard_stats["month_certificates"] else 0.0
	percent_exames_em_dia = ((aptos / total_exames) * 100) if total_exames else 0.0
	percent_afastados = ((dashboard_stats["inss_active"] / total_colaboradores) * 100) if total_colaboradores else 0.0
	taxa_acidentes_100 = (acidentes_total / total_colaboradores * 100) if total_colaboradores else 0.0

	risco_setor_score = Counter()
	for employee in employee_payloads:
		setor = employee.get("setor") or "Sem setor"
		status = (employee.get("saudeOcupacional", {}) or {}).get("status")
		if status == "high":
			risco_setor_score[setor] += 3
		elif status == "medium":
			risco_setor_score[setor] += 2
		else:
			risco_setor_score[setor] += 1

	return {
		"total_colaboradores": total_colaboradores,
		"status_counter": status_counter,
		"cid_counter": cid_counter,
		"afastamentos_setor": afastamentos_setor,
		"afastamentos_unidade": afastamentos_unidade,
		"afastamentos_por_colaborador": afastamentos_por_colaborador,
		"acidentes_setor": acidentes_setor,
		"acidentes_tipo": acidentes_tipo,
		"acidentes_total": acidentes_total,
		"taxa_frequencia": taxa_frequencia,
		"taxa_gravidade": taxa_gravidade,
		"dias_perdidos_total": dias_perdidos_total,
		"avg_tempo_afastamento": avg_tempo_afastamento,
		"horas_perdidas_total": horas_perdidas_total,
		"absenteismo_setor_text": absenteismo_setor_text,
		"mental_health_cids": mental_health_cids,
		"mental_health_away": mental_health_away,
		"restricoes_medicas": restricoes_medicas,
		"aptos": aptos,
		"inaptos": inaptos,
		"percent_exames_em_dia": percent_exames_em_dia,
		"percent_afastados": percent_afastados,
		"taxa_acidentes_100": taxa_acidentes_100,
		"risco_setor_score": risco_setor_score,
	}


def _module_metrics_from_facts(facts, dashboard_stats):
	month_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
	tendencia_rows = [
		{"mes": month_labels[index], "valor": value}
		for index, value in enumerate(dashboard_stats["certificates_series"])
	]
	absenteismo_setor_rows = [
		{"setor": setor, "taxa": taxa}
		for setor, taxa in facts["absenteismo_setor_text"].items()
	]
	indice_apto_rows = [
		{"status": "Aptos", "quantidade": facts["aptos"]},
		{"status": "Inaptos", "quantidade": facts["inaptos"]},
	]
	comparativo_afastamento_rows = [
		{"periodo": "Mês", "quantidade": dashboard_stats["inss_active"]},
		{"periodo": "Ano", "quantidade": sum(dashboard_stats["certificates_series"])},
	]
	exames_vencer_rows = [
		{"janela": "30 dias", "quantidade": "Não informado"},
		{"janela": "60 dias", "quantidade": dashboard_stats["exams60"]},
		{"janela": "90 dias", "quantidade": dashboard_stats["exams90"]},
	]

	executive_metrics = [
		{"label": "Total de colaboradores ativos", "value": facts["total_colaboradores"]},
		{"label": "% de colaboradores com exames em dia", "value": _format_percent(facts["percent_exames_em_dia"])},
		{"label": "% de colaboradores afastados", "value": _format_percent(facts["percent_afastados"])},
		{"label": "% de absenteísmo geral", "value": _format_percent(dashboard_stats["absenteeism_rate"])},
		{"label": "Taxa de acidentes por 100 colaboradores", "value": f"{facts['taxa_acidentes_100']:.2f}"},
		{"label": "Dias perdidos no mês", "value": facts["dias_perdidos_total"]},
		_table_metric_from_counter(
			"Ranking de setores com maior risco",
			facts["risco_setor_score"],
			"setor",
			"pontuacao",
			["Setor", "Pontuação"],
			["setor", "pontuacao"],
			3,
		),
		_table_metric("Tendência dos indicadores (12 meses)", tendencia_rows, ["Mês", "Indicador"], ["mes", "valor"]),
	]

	exam_metrics = [
		{"label": "Exames admissionais realizados", "value": facts["status_counter"].get("admissional", 0)},
		{"label": "Exames demissionais realizados", "value": facts["status_counter"].get("demissional", 0)},
		{"label": "Exames de retorno ao trabalho", "value": facts["status_counter"].get("retorno_trabalho", 0)},
		{"label": "Exames de mudança de função", "value": facts["status_counter"].get("mudanca_funcao", 0)},
		{"label": "Taxa de conformidade dos exames ocupacionais", "value": _format_percent(facts["percent_exames_em_dia"])},
		{"label": "Colaboradores sem ASO válido", "value": facts["inaptos"]},
	]

	health_metrics = [
		_table_metric_from_counter(
			"Ranking dos CIDs mais frequentes",
			facts["cid_counter"],
			"cid",
			"quantidade",
			["CID", "Ocorrências"],
			["cid", "quantidade"],
			5,
		),
		_table_metric_from_counter(
			"Principais causas de afastamento",
			facts["cid_counter"],
			"cid",
			"quantidade",
			["CID", "Ocorrências"],
			["cid", "quantidade"],
			3,
		),
		{"label": "Quantidade de colaboradores com restrições médicas", "value": facts["restricoes_medicas"]},
		{"label": "Controle de doenças ocupacionais", "value": facts["mental_health_cids"].total() if hasattr(facts["mental_health_cids"], "total") else sum(facts["mental_health_cids"].values())},
		{"label": "Casos suspeitos de doenças ocupacionais", "value": facts["mental_health_away"]},
		_table_metric("Índice de aptos x inaptos nos exames", indice_apto_rows, ["Status", "Quantidade"], ["status", "quantidade"]),
	]

	leave_metrics = [
		{"label": "Dias perdidos por afastamento", "value": facts["dias_perdidos_total"]},
		{"label": "Tempo médio de afastamento", "value": f"{facts['avg_tempo_afastamento']:.1f} dias"},
		_table_metric_from_counter(
			"Afastamentos por setor",
			facts["afastamentos_setor"],
			"setor",
			"quantidade",
			["Setor", "Afastamentos"],
			["setor", "quantidade"],
			10,
		),
		_table_metric_from_counter(
			"Afastamentos por unidade/filial",
			facts["afastamentos_unidade"],
			"unidade",
			"quantidade",
			["Unidade", "Afastamentos"],
			["unidade", "quantidade"],
			10,
		),
		_table_metric_from_counter(
			"Histórico de afastamentos por colaborador",
			facts["afastamentos_por_colaborador"],
			"colaborador",
			"quantidade",
			["Colaborador", "Afastamentos"],
			["colaborador", "quantidade"],
			10,
		),
		_table_metric("Comparativo mensal e anual de afastamentos", comparativo_afastamento_rows, ["Período", "Quantidade"], ["periodo", "quantidade"]),
	]

	accident_metrics = [
		{"label": "Acidentes com afastamento", "value": facts["afastamentos_setor"].total() if hasattr(facts["afastamentos_setor"], "total") else sum(facts["afastamentos_setor"].values())},
		{"label": "Acidentes sem afastamento", "value": max(facts["acidentes_total"] - dashboard_stats["inss_active"], 0)},
		{"label": "Taxa de frequência de acidentes", "value": f"{facts['taxa_frequencia']:.2f}"},
		{"label": "Taxa de gravidade de acidentes", "value": f"{facts['taxa_gravidade']:.2f}"},
		_table_metric_from_counter(
			"Acidentes por setor",
			facts["acidentes_setor"],
			"setor",
			"quantidade",
			["Setor", "Acidentes"],
			["setor", "quantidade"],
			10,
		),
		_table_metric_from_counter(
			"Acidentes por tipo de lesão",
			facts["acidentes_tipo"],
			"lesao",
			"quantidade",
			["Tipo de lesão", "Acidentes"],
			["lesao", "quantidade"],
			10,
		),
		{"label": "Acidentes por parte do corpo atingida", "value": "Não informado"},
		{"label": "Controle de emissão de CAT", "value": "Não informado"},
		{"label": "Dias perdidos por acidentes", "value": facts["dias_perdidos_total"]},
	]

	absenteeism_health_metrics = [
		_table_metric("Absenteísmo por setor", absenteismo_setor_rows, ["Setor", "Taxa"], ["setor", "taxa"]),
		{"label": "Absenteísmo por gestor", "value": "Não informado"},
		_table_metric_from_counter(
			"Absenteísmo por unidade",
			facts["afastamentos_unidade"],
			"unidade",
			"quantidade",
			["Unidade", "Ocorrências"],
			["unidade", "quantidade"],
			10,
		),
		_table_metric("Evolução mensal do absenteísmo", tendencia_rows, ["Mês", "Indicador"], ["mes", "valor"]),
		{"label": "Custo estimado do absenteísmo", "value": f"R$ {facts['horas_perdidas_total'] * 55:.2f}"},
		{"label": "Horas perdidas por absenteísmo", "value": f"{facts['horas_perdidas_total']:.1f}"},
		{"label": "Controle de vacinas obrigatórias", "value": "Não informado"},
		{"label": "Vacinas vencidas", "value": "Não informado"},
		{"label": "Vacinas próximas do vencimento", "value": "Não informado"},
		{"label": "Cobertura vacinal da empresa", "value": "Não informado"},
		{"label": "Colaboradores avaliados ergonomicamente", "value": "Não informado"},
		{"label": "Pendências de avaliações ergonômicas", "value": "Não informado"},
		{"label": "Não conformidades ergonômicas encontradas", "value": "Não informado"},
		{"label": "Plano de ação ergonômico", "value": "Não informado"},
		{"label": "Afastamentos relacionados à saúde mental", "value": facts["mental_health_away"]},
		_table_metric_from_counter(
			"Principais CIDs relacionados à saúde mental",
			facts["mental_health_cids"],
			"cid",
			"quantidade",
			["CID", "Ocorrências"],
			["cid", "quantidade"],
			10,
		),
		_table_metric_from_counter(
			"Evolução dos afastamentos psicológicos",
			facts["mental_health_cids"],
			"cid",
			"quantidade",
			["CID", "Ocorrências"],
			["cid", "quantidade"],
			12,
		),
		{"label": "Indicadores de acompanhamento psicológico", "value": "Não informado"},
		{"label": "Custos com exames ocupacionais", "value": f"R$ {facts['total_colaboradores'] * 120:.2f}"},
		{"label": "Custos com afastamentos", "value": f"R$ {facts['dias_perdidos_total'] * 180:.2f}"},
		{"label": "Custos com acidentes", "value": f"R$ {facts['acidentes_total'] * 500:.2f}"},
		{"label": "Custos por clínica prestadora", "value": "Não informado"},
		{"label": "Custos por unidade", "value": "Não informado"},
		_table_metric("Exames vencendo em 30, 60 e 90 dias", exames_vencer_rows, ["Janela", "Quantidade"], ["janela", "quantidade"]),
		{"label": "Exames vencidos", "value": dashboard_stats["expired_exams"]},
		{"label": "Retornos ao trabalho previstos para os próximos dias", "value": dashboard_stats["inss_active"]},
		{"label": "Vacinas vencendo", "value": "Não informado"},
		{"label": "Restrições médicas sem acompanhamento", "value": facts["restricoes_medicas"]},
		{"label": "Afastamentos próximos do prazo de alta", "value": dashboard_stats["inss_active"]},
	]

	return {
		"executive": executive_metrics,
		"exams": exam_metrics + health_metrics,
		"leave_inss": leave_metrics,
		"accidents": accident_metrics,
		"absenteeism_health": absenteeism_health_metrics,
	}


def build_dashboard_modules(employee_payloads, dashboard_stats):
	ensure_default_module_settings()
	facts = _build_dashboard_facts(employee_payloads, dashboard_stats)
	module_metrics = _module_metrics_from_facts(facts, dashboard_stats)

	module_settings = {
		item.module_key: item
		for item in DashboardModuleSetting.objects.all()
	}

	modules = []
	for default_order, (key, title, description) in enumerate(MODULE_REGISTRY):
		setting = module_settings.get(key)
		if setting and not setting.enabled:
			continue

		order = setting.order if setting else default_order
		modules.append({
			"key": key,
			"title": title,
			"description": description,
			"order": order,
			"metrics": module_metrics.get(key, []),
		})

	modules.sort(key=lambda item: item["order"])
	return modules


def get_employee_payload(employee_record):
	if not isinstance(employee_record.payload, dict):
		return {}

	return normalize_employee_payload(employee_record.payload)


def build_atestados_from_post(post_data):
	data_list = post_data.getlist("atestado_data")
	cid_list = post_data.getlist("atestado_cid")
	dias_list = post_data.getlist("atestado_dias")
	atestados = []

	for index, raw_date in enumerate(data_list):
		raw_cid = cid_list[index] if index < len(cid_list) else ""
		raw_dias = dias_list[index] if index < len(dias_list) else ""
		raw_date = raw_date.strip()
		raw_cid = raw_cid.strip()
		raw_dias = raw_dias.strip()

		if not raw_date and not raw_cid and not raw_dias:
			continue

		if not raw_date or not raw_cid or not raw_dias:
			raise ValueError("Preencha data, CID e dias de todos os atestados ou remova a linha em branco.")

		if not raw_dias.isdigit():
			raise ValueError("Os dias de afastamento devem ser um número inteiro.")

		atesto = {
			"data": raw_date,
			"cid": raw_cid,
			"dias": int(raw_dias),
		}
		atestados.append(atesto)

	return atestados


def dashboard(request):
	hidden_dashboard_card_keys = set()
	if request.user.is_authenticated:
		layout, _ = UserDashboardLayout.objects.get_or_create(usuario=request.user)
		hidden_dashboard_card_keys = _get_hidden_dashboard_card_keys(layout)
	employees_payloads = get_active_employee_payloads()

	context = {
		"hidden_dashboard_card_keys": sorted(hidden_dashboard_card_keys),
		"employees_payloads": employees_payloads,
		"dashboard_stats": build_dashboard_stats(employees_payloads),
	}
	context["dashboard_modules"] = build_dashboard_modules(employees_payloads, context["dashboard_stats"])
	context["active_module_key"] = context["dashboard_modules"][0]["key"] if context["dashboard_modules"] else ""
	return render(request, 'health/index.html', context)


def _get_hidden_dashboard_card_keys(layout):
	return {card_key for card_key in layout.cards_ocultos_dashboard if card_key in SUMMARY_DASHBOARD_CARD_KEYS}


def _get_visible_dashboard_cards(hidden_dashboard_card_keys):
	return [card for card in SUMMARY_DASHBOARD_CARDS if card["key"] not in hidden_dashboard_card_keys]


def funcionarios(request):
	context = {
		"employees_payloads": get_active_employee_payloads(),
		"is_admin": user_is_admin(request.user),
	}
	return render(request, 'health/funcionarios/funcionarios.html', context)


@login_required
def editar_funcionario(request, employee_id):
	if not user_is_admin(request.user):
		return HttpResponseForbidden("Somente administrador pode editar funcionários.")

	record = get_object_or_404(EmployeeRecord, id=employee_id)
	payload = get_employee_payload(record)
	saude = payload.get("saudeOcupacional", {})
	af = saude.get("afastamentoINSS", {})
	exames = saude.get("exames", {})
	acidentes = saude.get("acidentes", {})
	absenteismo = saude.get("absenteismo", {})

	if request.method == "POST":
		try:
			updated_atestados = build_atestados_from_post(request.POST)
		except ValueError as exc:
			messages.error(request, str(exc))
		else:
			payload["nome"] = request.POST.get("nome", "").strip()
			payload["cargo"] = request.POST.get("cargo", "").strip()
			payload["setor"] = request.POST.get("setor", "").strip()
			saude["status"] = request.POST.get("status", "low")
			saude["afastamentoINSS"] = {
				"ativo": request.POST.get("afastamento_ativo") == "on",
				"dataAfastamento": request.POST.get("data_afastamento") or None,
				"previsaoRetorno": request.POST.get("previsao_retorno") or None,
			}
			saude["exames"] = {
				"status": request.POST.get("exame_status", "em_dia"),
				"proximoPeriodico": request.POST.get("proximo_periodico") or None,
				"realizadoNoMes": request.POST.get("exame_realizado_no_mes") == "on",
			}
			saude["acidentes"] = {
				"quantidadeAno": int(request.POST.get("acidentes_quantidade", "0") or 0),
				"ultimoTipo": request.POST.get("ultimo_tipo", "").strip(),
				"dataUltimo": request.POST.get("data_ultimo_acidente") or None,
			}
			saude["atestados"] = updated_atestados
			saude["absenteismo"] = calculate_absenteeism_from_atestados(updated_atestados)
			payload["saudeOcupacional"] = saude
			record.payload = payload
			record.save(update_fields=["payload"])
			messages.success(request, "Funcionário atualizado com sucesso.")
			return redirect("health:funcionarios")

	context = {
		"employee": payload,
		"employee_id": record.id,
		"status_options": [
			("low", "Estável"),
			("medium", "Atenção"),
			("high", "Crítico"),
		],
		"exame_status_options": [
			("em_dia", "Em dia"),
			("vence60", "Vence em 60 dias"),
			("vence90", "Vence em 90 dias"),
			("vencido", "Vencido"),
		],
		"atestados": saude.get("atestados", []),
		"afastamento": af,
		"exames": exames,
		"acidentes": acidentes,
		"absenteismo": absenteismo,
	}
	return render(request, "health/funcionarios/funcionario-editar.html", context)


def funcionarios_detalhes(request):
	context = {
		"employees_payloads": get_active_employee_payloads(),
		"is_admin": user_is_admin(request.user),
	}
	return render(request, 'health/funcionarios/funcionarios-detalhes.html', context)


def relatorios(request):
	context = {
		"employees_payloads": get_active_employee_payloads(),
	}
	return render(request, 'health/relatorios/relatorios.html', context)


def configuracoes(request):
	return render(request, 'health/configuracoes/configuracoes.html')


def user_is_admin(user):
	return user.is_superuser or user.is_staff or user.groups.filter(name="administrador").exists()


def ensure_default_dashboard_structure():
	if DashboardItem.objects.exists():
		return

	defaults = [
		("Atestados Médicos", ["CID", "Quantidade", "Observações"]),
		("Afastamentos INSS", ["Data de afastamento", "Previsão de retorno"]),
		("Exames Periódicos", ["Status do exame", "Data limite"]),
		("Acidentes", ["Tipo", "Descrição"]),
		("Absenteísmo", ["Taxa mensal", "Horas perdidas"]),
	]

	for item_index, (item_name, fields) in enumerate(defaults):
		item = DashboardItem.objects.create(nome=item_name, posicao=item_index)
		for field_index, field_name in enumerate(fields):
			DashboardField.objects.create(item=item, nome=field_name, posicao=field_index)


@login_required
def painel_usuario(request):
	ensure_default_dashboard_structure()

	is_admin = user_is_admin(request.user)
	layout, _ = UserDashboardLayout.objects.get_or_create(usuario=request.user)
	hidden_dashboard_card_keys = _get_hidden_dashboard_card_keys(layout)

	items_qs = DashboardItem.objects.filter(ativo=True).prefetch_related("campos")
	items_by_id = {item.id: item for item in items_qs}
	ordered_ids = [item_id for item_id in layout.ordem_itens if item_id in items_by_id]
	remaining_ids = [item.id for item in items_qs if item.id not in ordered_ids]
	ordered_items = [items_by_id[item_id] for item_id in ordered_ids + remaining_ids]
	hidden_item_ids = {item_id for item_id in layout.itens_ocultos if item_id in items_by_id}

	context = {
		"is_admin": is_admin,
		"layout": layout,
		"ordered_items": ordered_items,
		"hidden_item_ids": hidden_item_ids,
		"dashboard_cards": SUMMARY_DASHBOARD_CARDS,
		"hidden_dashboard_card_keys": sorted(hidden_dashboard_card_keys),
		"employees_payloads": get_active_employee_payloads(),
	}
	return render(request, "health/painel/painel.html", context)


@login_required
@require_POST
def salvar_layout(request):
	try:
		payload = json.loads(request.body.decode("utf-8"))
	except (TypeError, json.JSONDecodeError):
		return JsonResponse({"ok": False, "error": "Payload inválido."}, status=400)

	order = payload.get("order", [])
	view_mode = payload.get("view_mode", "cards")
	hidden_ids = payload.get("hidden_ids", [])

	if not isinstance(order, list):
		return JsonResponse({"ok": False, "error": "Ordem inválida."}, status=400)

	if not isinstance(hidden_ids, list):
		return JsonResponse({"ok": False, "error": "Lista de ocultos inválida."}, status=400)

	hidden_dashboard_cards = payload.get("hidden_dashboard_cards", [])
	if not isinstance(hidden_dashboard_cards, list):
		return JsonResponse({"ok": False, "error": "Lista de cards ocultos inválida."}, status=400)

	valid_mode = view_mode in {"cards", "grid"}
	if not valid_mode:
		return JsonResponse({"ok": False, "error": "Modo inválido."}, status=400)

	layout, _ = UserDashboardLayout.objects.get_or_create(usuario=request.user)
	layout.ordem_itens = [int(item_id) for item_id in order if str(item_id).isdigit()]
	layout.itens_ocultos = [int(item_id) for item_id in hidden_ids if str(item_id).isdigit()]
	layout.cards_ocultos_dashboard = [str(card_key) for card_key in hidden_dashboard_cards if str(card_key) in SUMMARY_DASHBOARD_CARD_KEYS]
	layout.modo_visualizacao = view_mode
	layout.save(update_fields=["ordem_itens", "modo_visualizacao", "itens_ocultos", "cards_ocultos_dashboard"])

	return JsonResponse({"ok": True})


@login_required
@require_POST
def adicionar_ou_atualizar_info(request, campo_id):
	campo = get_object_or_404(DashboardField, id=campo_id)
	valor = request.POST.get("valor", "").strip()

	if not valor:
		messages.error(request, "Informe um valor antes de salvar.")
		return redirect("health:painel")

	DashboardEntry.objects.update_or_create(
		campo=campo,
		usuario=request.user,
		defaults={"valor": valor},
	)
	messages.success(request, "Informação salva com sucesso.")
	return redirect("health:painel")


@login_required
@require_POST
def editar_info(request, entry_id):
	entry = get_object_or_404(DashboardEntry, id=entry_id)
	is_admin = user_is_admin(request.user)

	if not is_admin and entry.usuario_id != request.user.id:
		return HttpResponseForbidden("Sem permissão para editar esta informação.")

	valor = request.POST.get("valor", "").strip()
	if not valor:
		messages.error(request, "Informe um valor válido para atualizar.")
		return redirect("health:painel")

	entry.valor = valor
	entry.save(update_fields=["valor", "atualizado_em"])
	messages.success(request, "Informação atualizada.")
	return redirect("health:painel")


@login_required
@require_POST
def remover_info(request, entry_id):
	entry = get_object_or_404(DashboardEntry, id=entry_id)
	is_admin = user_is_admin(request.user)

	if not is_admin and entry.usuario_id != request.user.id:
		return HttpResponseForbidden("Sem permissão para remover esta informação.")

	entry.delete()
	messages.success(request, "Informação removida.")
	return redirect("health:painel")


@login_required
@require_POST
def renomear_item(request, item_id):
	if not user_is_admin(request.user):
		return HttpResponseForbidden("Somente administrador pode renomear itens.")

	item = get_object_or_404(DashboardItem, id=item_id)
	novo_nome = request.POST.get("nome", "").strip()
	if not novo_nome:
		messages.error(request, "Nome do item não pode ficar vazio.")
		return redirect("health:painel")

	item.nome = novo_nome
	item.save(update_fields=["nome"])
	messages.success(request, "Item renomeado.")
	return redirect("health:painel")


@login_required
@require_POST
def renomear_campo(request, campo_id):
	if not user_is_admin(request.user):
		return HttpResponseForbidden("Somente administrador pode renomear campos.")

	campo = get_object_or_404(DashboardField, id=campo_id)
	novo_nome = request.POST.get("nome", "").strip()
	if not novo_nome:
		messages.error(request, "Nome do campo não pode ficar vazio.")
		return redirect("health:painel")

	campo.nome = novo_nome
	campo.save(update_fields=["nome"])
	messages.success(request, "Campo renomeado.")
	return redirect("health:painel")
