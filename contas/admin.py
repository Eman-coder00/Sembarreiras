from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CepLocal,
    LogAuditoriaConta,
    PerfilPCD,
    TokenRecuperacaoSenha,
    Usuario,
    VinculoCuidador,
)

admin.site.register(Usuario, UserAdmin)


@admin.register(PerfilPCD)
class PerfilPCDAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "usuario",
        "tipo_deficiencia",
        "tamanho_toque",
        "timeout_tela",
        "alto_contraste",
        "municipio",
        "uf",
    )
    list_select_related = ("usuario",)  # type: ignore[assignment]
    search_fields = (  # type: ignore[assignment]
        "usuario__cpf",
        "usuario__nome_completo",
        "cep",
        "bairro",
    )


@admin.register(VinculoCuidador)
class VinculoCuidadorAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "cuidador",
        "titular_pcd",
        "grau_parentesco",
        "status",
        "criado_em",
    )
    list_filter = ("status", "grau_parentesco")  # type: ignore[assignment]
    list_select_related = ("cuidador", "titular_pcd")  # type: ignore[assignment]

    def has_add_permission(self, request):
        return False


@admin.register(LogAuditoriaConta)
class LogAuditoriaContaAdmin(admin.ModelAdmin):
    list_display = ("evento", "usuario", "ip", "criado_em")  # type: ignore[assignment]
    list_filter = ("evento",)  # type: ignore[assignment]
    list_select_related = ("usuario",)  # type: ignore[assignment]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CepLocal)
class CepLocalAdmin(admin.ModelAdmin):
    list_display = ("cep", "logradouro", "bairro", "municipio", "uf")  # type: ignore[assignment]
    search_fields = ("cep", "logradouro", "bairro")  # type: ignore[assignment]


@admin.register(TokenRecuperacaoSenha)
class TokenRecuperacaoSenhaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "utilizado", "expira_em", "criado_em")  # type: ignore[assignment]
    list_select_related = ("usuario",)  # type: ignore[assignment]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
