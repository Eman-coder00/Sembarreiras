from django.urls import path

from .views import (
    ComprovanteDigitalView,
    ConsultaCancelarView,
    ConsultaCreateView,
    ConsultaDetailView,
    ConsultaListView,
    ConsultaRemarcarView,
    PortariaValidarQRView,
    TransporteCancelarView,
    TransporteSolicitarView,
)

app_name = "agendamentos"

urlpatterns = [
    path("", ConsultaListView.as_view(), name="lista"),
    path("novo/", ConsultaCreateView.as_view(), name="criar"),
    path("portaria/validar/", PortariaValidarQRView.as_view(), name="validar_qr"),
    path("<str:protocolo>/", ConsultaDetailView.as_view(), name="detalhe"),
    path(
        "<str:protocolo>/cancelar/",
        ConsultaCancelarView.as_view(),
        name="cancelar",
    ),
    path(
        "<str:protocolo>/remarcar/",
        ConsultaRemarcarView.as_view(),
        name="remarcar",
    ),
    path(
        "<str:protocolo>/transporte/",
        TransporteSolicitarView.as_view(),
        name="solicitar_transporte",
    ),
    path(
        "<str:protocolo>/transporte/cancelar/",
        TransporteCancelarView.as_view(),
        name="cancelar_transporte",
    ),
    path(
        "<str:protocolo>/comprovante/",
        ComprovanteDigitalView.as_view(),
        name="comprovante",
    ),
]
