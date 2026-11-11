from django.contrib import admin

from .models import ContatoEmergencia, OcorrenciaPanico


@admin.register(ContatoEmergencia)
class ContatoEmergenciaAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "titular_pcd",
        "prioridade",
        "nome",
        "telefone",
        "parentesco",
        "status",
    )
    list_filter = ("status", "parentesco", "prioridade")  # type: ignore[assignment]
    search_fields = ("nome", "telefone", "titular_pcd__cpf", "titular_pcd__nome_completo")  # type: ignore[assignment]
    list_select_related = ("titular_pcd",)  # type: ignore[assignment]


@admin.register(OcorrenciaPanico)
class OcorrenciaPanicoAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "codigo",
        "titular_pcd",
        "status",
        "latitude",
        "longitude",
        "criado_em",
        "finalizado_em",
    )
    list_filter = ("status", "criado_em")  # type: ignore[assignment]
    search_fields = (  # type: ignore[assignment]
        "codigo",
        "titular_pcd__cpf",
        "titular_pcd__nome_completo",
        "endereco_aproximado",
    )
    readonly_fields = (  # type: ignore[assignment]
        "codigo",
        "titular_pcd",
        "latitude",
        "longitude",
        "endereco_aproximado",
        "status",
        "contatos_notificados",
        "mensagem_enviada",
        "criado_em",
        "finalizado_em",
    )
    list_select_related = ("titular_pcd",)  # type: ignore[assignment]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

