from django.urls import path

from .views import (
    BotaoPanicoView,
    CancelarPanicoView,
    ContagemRegressivaView,
    ContatoEmergenciaDeleteView,
    ContatoEmergenciaListView,
    ContatoEmergenciaUpdateView,
    DispararPanicoView,
    HistoricoPanicoView,
)

app_name = "emergencia"

urlpatterns = [
    path("contatos/", ContatoEmergenciaListView.as_view(), name="contatos"),
    path(
        "contatos/<int:contato_id>/editar/",
        ContatoEmergenciaUpdateView.as_view(),
        name="editar_contato",
    ),
    path(
        "contatos/<int:contato_id>/excluir/",
        ContatoEmergenciaDeleteView.as_view(),
        name="excluir_contato",
    ),
    path("panico/", BotaoPanicoView.as_view(), name="panico"),
    path(
        "panico/<int:ocorrencia_id>/contagem/",
        ContagemRegressivaView.as_view(),
        name="contagem",
    ),
    path(
        "panico/<int:ocorrencia_id>/cancelar/",
        CancelarPanicoView.as_view(),
        name="cancelar",
    ),
    path(
        "panico/<int:ocorrencia_id>/disparar/",
        DispararPanicoView.as_view(),
        name="disparar",
    ),
    path("historico/", HistoricoPanicoView.as_view(), name="historico"),
]
