from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'health'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', views.dashboard, name='dashboard'),
    path('funcionarios/', views.funcionarios, name='funcionarios'),
    path('funcionarios/adicionar/', views.adicionar_funcionario, name='adicionar-funcionario'),
    path('funcionarios/<int:employee_id>/remover/', views.remover_funcionario, name='remover-funcionario'),
    path('funcionarios/detalhes/', views.funcionarios_detalhes, name='funcionarios-detalhes'),
    path('funcionarios/<int:employee_id>/editar/', views.editar_funcionario, name='editar-funcionario'),
    path('relatorios/', views.relatorios, name='relatorios'),
    path('configuracoes/', views.configuracoes, name='configuracoes'),

    path('painel/', views.painel_usuario, name='painel'),
    path('painel/importar-planilha/', views.importar_funcionarios_planilha, name='importar-funcionarios-planilha'),
    path('painel/exportar/json/', views.exportar_funcionarios_json, name='exportar-funcionarios-json'),
    path('painel/exportar/xml/', views.exportar_funcionarios_xml, name='exportar-funcionarios-xml'),
    path('painel/layout/', views.salvar_layout, name='salvar-layout'),
    path('painel/item/<int:item_id>/renomear/', views.renomear_item, name='renomear-item'),
    path('painel/campo/<int:campo_id>/renomear/', views.renomear_campo, name='renomear-campo'),
]
