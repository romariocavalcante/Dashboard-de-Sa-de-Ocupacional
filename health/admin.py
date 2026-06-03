from django.contrib import admin

from .models import DashboardField, DashboardItem, DashboardModuleSetting, EmployeeRecord, UserDashboardLayout


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
	list_display = ("id", "nome_display", "cargo_display", "setor_display", "ativo", "ordem")
	list_editable = ("ativo", "ordem")

	@admin.display(description="Nome")
	def nome_display(self, obj):
		return obj.nome

	@admin.display(description="Cargo")
	def cargo_display(self, obj):
		return obj.cargo

	@admin.display(description="Setor")
	def setor_display(self, obj):
		return obj.setor


@admin.register(UserDashboardLayout)
class UserDashboardLayoutAdmin(admin.ModelAdmin):
	list_display = ("id", "usuario", "modo_visualizacao")
	search_fields = ("usuario__username",)


@admin.register(DashboardModuleSetting)
class DashboardModuleSettingAdmin(admin.ModelAdmin):
	list_display = ("id", "module_key", "enabled", "order")
	list_editable = ("enabled", "order")
	list_filter = ("enabled",)
