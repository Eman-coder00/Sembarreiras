from django.urls import path

from .views import (
    LinhaAcessivelConsultaView,
    MapaAcessivelView,
    VeiculoRastreamentoView,
)

app_name = "transporte"

urlpatterns = [
    path("", LinhaAcessivelConsultaView.as_view(), name="consulta"),
    path("mapa/", MapaAcessivelView.as_view(), name="mapa"),
    path(
        "veiculos/<str:prefixo>/",
        VeiculoRastreamentoView.as_view(),
        name="rastrear",
    ),
]
