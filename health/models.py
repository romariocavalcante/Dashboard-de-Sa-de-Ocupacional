from django.conf import settings
from django.db import models


class DashboardItem(models.Model):
	nome = models.CharField(max_length=120)
	posicao = models.PositiveIntegerField(default=0)
	ativo = models.BooleanField(default=True)

	class Meta:
		ordering = ["posicao", "id"]

	def __str__(self):
		return self.nome


class DashboardField(models.Model):
	item = models.ForeignKey(DashboardItem, on_delete=models.CASCADE, related_name="campos")
	nome = models.CharField(max_length=120)
	posicao = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ["posicao", "id"]

	def __str__(self):
		return f"{self.item.nome} - {self.nome}"


class DashboardEntry(models.Model):
	campo = models.ForeignKey(DashboardField, on_delete=models.CASCADE, related_name="entradas")
	usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="entradas_dashboard")
	valor = models.TextField()
	criado_em = models.DateTimeField(auto_now_add=True)
	atualizado_em = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ("campo", "usuario")
		ordering = ["-atualizado_em"]

	def __str__(self):
		return f"{self.usuario} - {self.campo.nome}"


class EmployeeRecord(models.Model):
	payload = models.JSONField(default=dict)
	ativo = models.BooleanField(default=True)
	ordem = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ["ordem", "id"]

	def __str__(self):
		return self.payload.get("nome", f"Funcionário {self.pk}")

	@property
	def nome(self):
		return self.payload.get("nome", "")

	@property
	def funcao(self):
		return self.payload.get("funcao") or self.payload.get("cargo", "")

	@property
	def secao(self):
		return self.payload.get("secao") or self.payload.get("setor", "")

	@property
	def dt_inicio(self):
		return self.payload.get("dt_inicio")

	@property
	def dt_final(self):
		return self.payload.get("dt_final")

	@property
	def dias_afastados(self):
		return self.payload.get("dias_afastados")

	@property
	def motivo(self):
		return self.payload.get("motivo")

	@property
	def cid(self):
		return self.payload.get("cid")

	@property
	def qtd_atestados(self):
		return self.payload.get("qtd_atestados")


class UserDashboardLayout(models.Model):
	MODO_CHOICES = (
		("cards", "Cards"),
		("grid", "Grade"),
	)

	usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="layout_dashboard")
	modo_visualizacao = models.CharField(max_length=20, choices=MODO_CHOICES, default="cards")
	ordem_itens = models.JSONField(default=list, blank=True)
	itens_ocultos = models.JSONField(default=list, blank=True)
	cards_ocultos_dashboard = models.JSONField(default=list, blank=True)

	def __str__(self):
		return f"Layout de {self.usuario}"


class DashboardModuleSetting(models.Model):
	MODULE_CHOICES = (
		("executive", "Visão Executiva (KPIs)"),
		("exams", "Exames Ocupacionais"),
		("leave_inss", "Afastamentos e INSS"),
		("accidents", "Acidentes e CAT"),
		("absenteeism_health", "Absenteísmo e Saúde dos Colaboradores"),
	)

	module_key = models.CharField(max_length=40, choices=MODULE_CHOICES, unique=True)
	enabled = models.BooleanField(default=True)
	order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ["order", "id"]

	def __str__(self):
		return self.get_module_key_display()
