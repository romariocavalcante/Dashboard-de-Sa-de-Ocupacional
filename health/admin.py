from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .models import DashboardField, DashboardItem, DashboardModuleSetting, EmployeeRecord, UserDashboardLayout
from .views import (
	_build_employee_payload_from_row,
	_normalize_employee_key,
	_read_employee_spreadsheet,
	_read_employee_spreadsheet_path,
)


@admin.register(DashboardItem)
class DashboardItemAdmin(admin.ModelAdmin):
	list_display = ("id", "nome", "posicao", "ativo")
	list_editable = ("posicao", "ativo")
	search_fields = ("nome",)


@admin.register(DashboardField)
class DashboardFieldAdmin(admin.ModelAdmin):
	list_display = ("id", "nome", "item", "posicao")
	list_editable = ("posicao",)
	search_fields = ("nome", "item__nome")
	list_filter = ("item",)


@admin.register(EmployeeRecord)
class EmployeeRecordAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"chapa_display",
		"nome_display",
		"funcao_display",
		"dt_inicio_display",
		"dt_final_display",
		"dias_afastados_display",
		"motivo_display",
		"cid_display",
		"secao_display",
		"qtd_atestados_display",
		"ativo",
		"ordem",
	)
	list_editable = ("ativo", "ordem")
	change_list_template = "admin/health/employeerecord/change_list.html"

	class ImportForm(forms.Form):
		planilha = forms.FileField(required=False)
		use_default = forms.BooleanField(required=False)

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path("importar/", self.admin_site.admin_view(self.importar_planilha), name="health_employeerecord_import"),
		]
		return custom_urls + urls

	def importar_planilha(self, request):
		if not self.has_add_permission(request):
			self.message_user(request, "Sem permissao para importar.", level=messages.ERROR)
			return redirect("..")

		form = self.ImportForm()
		if request.method == "POST":
			form = self.ImportForm(request.POST, request.FILES)
			if form.is_valid():
				use_default = form.cleaned_data.get("use_default")
				planilha = form.cleaned_data.get("planilha")

				try:
					if use_default and not planilha:
						data_dir = Path(settings.BASE_DIR) / "health" / "static" / "health" / "data-js"
						candidates = sorted(data_dir.glob("*.xlsx"))
						if not candidates:
							self.message_user(request, "Nenhuma planilha .xlsx encontrada em data-js.", level=messages.ERROR)
							return redirect(".")
						planilha_path = None
						for candidate in candidates:
							if "controle" in candidate.name.lower():
								planilha_path = candidate
								break
						if planilha_path is None:
							planilha_path = candidates[0]
						rows = _read_employee_spreadsheet_path(planilha_path)
					elif planilha:
						rows = _read_employee_spreadsheet(planilha)
					else:
						self.message_user(request, "Selecione um arquivo para importar.", level=messages.ERROR)
						return redirect(".")
				except Exception as exc:
					self.message_user(request, f"Falha ao processar planilha: {exc}", level=messages.ERROR)
					return redirect(".")

				created_count = 0
				updated_count = 0
				skipped_count = 0
				row_errors = 0
				next_order = (EmployeeRecord.objects.order_by("-ordem").values_list("ordem", flat=True).first() or 0) + 1
				grouped_payloads = {}
				grouped_order = {}

				def merge_payloads(base_payload, incoming_payload):
					for key in ("chapa", "funcao", "secao"):
						if not base_payload.get(key) and incoming_payload.get(key):
							base_payload[key] = incoming_payload.get(key)

					if base_payload.get("qtd_atestados") is None and incoming_payload.get("qtd_atestados") is not None:
						base_payload["qtd_atestados"] = incoming_payload.get("qtd_atestados")

					base_saude = base_payload.get("saudeOcupacional", {})
					incoming_saude = incoming_payload.get("saudeOcupacional", {})
					base_atestados = list(base_saude.get("atestados") or [])
					incoming_atestados = list(incoming_saude.get("atestados") or [])
					if incoming_atestados:
						base_atestados.extend(incoming_atestados)
						base_saude["atestados"] = base_atestados
						base_payload["saudeOcupacional"] = base_saude

					return base_payload

				for raw_row in rows:
					try:
						payload, row = _build_employee_payload_from_row(raw_row)
					except ValueError:
						row_errors += 1
						continue

					if not payload.get("nome"):
						skipped_count += 1
						continue

					record_id = row.get("id")
					ordem = row.get("ordem")
					if record_id:
						updated = EmployeeRecord.objects.filter(id=record_id).update(
							payload=payload,
							ativo=True,
							ordem=ordem if ordem is not None else next_order,
						)
						if updated:
							updated_count += 1
							if ordem is None:
								next_order += 1
							continue

					key = _normalize_employee_key(payload.get("nome"))
					if key in grouped_payloads:
						grouped_payloads[key] = merge_payloads(grouped_payloads[key], payload)
						continue

					grouped_payloads[key] = payload
					grouped_order[key] = ordem

				for key, payload in grouped_payloads.items():
					ordem = grouped_order.get(key)
					EmployeeRecord.objects.create(
						payload=payload,
						ativo=True,
						ordem=ordem if ordem is not None else next_order,
					)
					created_count += 1
					if ordem is None:
						next_order += 1

				if created_count or updated_count:
					self.message_user(
						request,
						f"Importacao concluida. Criados: {created_count}, atualizados: {updated_count}, ignorados: {skipped_count}.",
						level=messages.SUCCESS,
					)
				else:
					self.message_user(request, "Nenhum funcionario foi importado.", level=messages.WARNING)

				if row_errors:
					self.message_user(request, f"Linhas com erro: {row_errors}.", level=messages.WARNING)

				return redirect("..")

		context = {
			"form": form,
			"title": "Importar funcionarios",
			"opts": self.model._meta,
			"media": self.media,
		}
		return render(request, "admin/health/employeerecord/import.html", context)

	@admin.display(description="Nome")
	def nome_display(self, obj):
		return obj.nome

	@admin.display(description="Chapa")
	def chapa_display(self, obj):
		return obj.payload.get("chapa", "")

	@admin.display(description="Funcao")
	def funcao_display(self, obj):
		return obj.funcao

	@admin.display(description="Dt inicio")
	def dt_inicio_display(self, obj):
		return obj.dt_inicio

	@admin.display(description="Dt final")
	def dt_final_display(self, obj):
		return obj.dt_final

	@admin.display(description="Dias afastados")
	def dias_afastados_display(self, obj):
		return obj.dias_afastados

	@admin.display(description="Motivo")
	def motivo_display(self, obj):
		return obj.motivo

	@admin.display(description="CID")
	def cid_display(self, obj):
		return obj.cid

	@admin.display(description="Secao")
	def secao_display(self, obj):
		return obj.secao

	@admin.display(description="Qtd atestados")
	def qtd_atestados_display(self, obj):
		return obj.qtd_atestados


@admin.register(UserDashboardLayout)
class UserDashboardLayoutAdmin(admin.ModelAdmin):
	list_display = ("id", "usuario", "modo_visualizacao")
	search_fields = ("usuario__username",)


@admin.register(DashboardModuleSetting)
class DashboardModuleSettingAdmin(admin.ModelAdmin):
	list_display = ("id", "module_key", "enabled", "order")
	list_editable = ("enabled", "order")
	list_filter = ("enabled",)
