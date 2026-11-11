"""Configuração de URLs raiz do projeto SemBarreiras."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("contas.urls")),
    path("emergencia/", include("emergencia.urls")),
    path("transporte/", include("transporte.urls")),
    path("agendamentos/", include("agendamentos.urls")),
    path("equipamentos/", include("equipamentos.urls")),
]

