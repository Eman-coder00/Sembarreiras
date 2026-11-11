from django.urls import path

from .views import (
    AcessibilidadeView,
    CadastroCuidadorView,
    CadastroPCDView,
    ConsultarCepView,
    ContaInativarView,
    EntrarView,
    HomeView,
    NotificacoesView,
    PainelInicialView,
    PerfilEditarView,
    SairView,
    SenhaRecuperarView,
    SenhaRedefinirView,
    VinculoConfirmarView,
    VinculoListView,
    VinculoRevogarView,
)

app_name = "contas"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("notificacoes/", NotificacoesView.as_view(), name="notificacoes"),
    path("conta/", PainelInicialView.as_view(), name="painel"),
    path("entrar/", EntrarView.as_view(), name="entrar"),
    path("sair/", SairView.as_view(), name="sair"),
    path("cadastro/pcd/", CadastroPCDView.as_view(), name="cadastro_pcd"),
    path(
        "cadastro/cuidador/",
        CadastroCuidadorView.as_view(),
        name="cadastro_cuidador",
    ),
    path("cep/consultar/", ConsultarCepView.as_view(), name="consultar_cep"),
    path("perfil/", PerfilEditarView.as_view(), name="perfil"),
    path(
        "perfil/acessibilidade/",
        AcessibilidadeView.as_view(),
        name="acessibilidade",
    ),
    path("perfil/inativar/", ContaInativarView.as_view(), name="inativar"),
    path("vinculos/", VinculoListView.as_view(), name="vinculos"),
    path(
        "vinculos/<int:vinculo_id>/confirmar/",
        VinculoConfirmarView.as_view(),
        name="confirmar_vinculo",
    ),
    path(
        "vinculos/<int:vinculo_id>/revogar/",
        VinculoRevogarView.as_view(),
        name="revogar_vinculo",
    ),
    path("senha/recuperar/", SenhaRecuperarView.as_view(), name="recuperar_senha"),
    path("senha/redefinir/", SenhaRedefinirView.as_view(), name="redefinir_senha"),
]
