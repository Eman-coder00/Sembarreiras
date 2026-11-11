from django.urls import path

from .views import LinhaAcessivelConsultaView, VeiculoRastreamentoView

app_name = "transporte"

urlpatterns = [
    path("", LinhaAcessivelConsultaView.as_view(), name="consulta"),
    path(
        "veiculos/<str:prefixo>/",
        VeiculoRastreamentoView.as_view(),
        name="rastrear",
    ),
]
