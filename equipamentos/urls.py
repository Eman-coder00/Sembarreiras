from django.urls import path

from .views import (
    EquipamentoAnexoDownloadView,
    EquipamentoCreateView,
    EquipamentoDetailView,
    EquipamentoListView,
    EquipamentoPrazoView,
)

app_name = "equipamentos"

urlpatterns = [
    path("", EquipamentoListView.as_view(), name="lista"),
    path("solicitar/", EquipamentoCreateView.as_view(), name="solicitar"),
    path("<str:protocolo>/", EquipamentoDetailView.as_view(), name="detalhe"),
    path(
        "<str:protocolo>/anexo/<str:tipo_documento>/",
        EquipamentoAnexoDownloadView.as_view(),
        name="baixar_anexo",
    ),
    path(
        "<str:protocolo>/prazo/",
        EquipamentoPrazoView.as_view(),
        name="gerenciar_prazo",
    ),
]
