from django.contrib import admin

from .models import (
    EventoLinhaTempoEquipamento,
    SolicitacaoEquipamento,
    StatusSolicitacaoEquipamento,
)
from .services import EquipamentoService


@admin.register(SolicitacaoEquipamento)
class SolicitacaoEquipamentoAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "protocolo",
        "beneficiario_pcd",
        "tipo_equipamento",
        "status",
        "data_vencimento_emprestimo",
        "acao_devolucao",
        "criado_em",
    )
    list_filter = ("status", "tipo_equipamento", "acao_devolucao")  # type: ignore[assignment]
    search_fields = (  # type: ignore[assignment]
        "protocolo",
        "beneficiario_pcd__cpf",
        "beneficiario_pcd__nome_completo",
    )
    readonly_fields = ("protocolo", "criado_em", "atualizado_em")  # type: ignore[assignment]
    list_select_related = ("beneficiario_pcd", "solicitado_por")  # type: ignore[assignment]
    actions = ["aprovar_para_retirada", "marcar_como_entregue"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Aprovar solicitações para retirada na ADEFAL")
    def aprovar_para_retirada(self, request, queryset):
        for solicitacao in queryset:
            EquipamentoService.atualizar_status_triagem(
                operador_staff=request.user,
                protocolo=solicitacao.protocolo,
                novo_status=StatusSolicitacaoEquipamento.APROVADO_RETIRADA,
                parecer_tecnico="Aprovado pela equipe técnica da ADEFAL.",
            )

    @admin.action(description="Marcar como entregue em empréstimo vigente")
    def marcar_como_entregue(self, request, queryset):
        for solicitacao in queryset:
            EquipamentoService.atualizar_status_triagem(
                operador_staff=request.user,
                protocolo=solicitacao.protocolo,
                novo_status=StatusSolicitacaoEquipamento.DEFERIDO_ENTREGUE,
                parecer_tecnico="Equipamento entregue ao beneficiário mediante termo de empréstimo.",
            )


@admin.register(EventoLinhaTempoEquipamento)
class EventoLinhaTempoEquipamentoAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "status", "descricao", "registrado_por", "criado_em")  # type: ignore[assignment]
    list_filter = ("status",)  # type: ignore[assignment]
    search_fields = ("solicitacao__protocolo", "descricao")  # type: ignore[assignment]
    list_select_related = ("solicitacao", "registrado_por")  # type: ignore[assignment]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

