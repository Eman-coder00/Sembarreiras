from django.contrib import admin

from .models import (
    Consulta,
    SolicitacaoTransporte,
    VagaAgendaADEFAL,
    VagaFrotaAdaptada,
)


@admin.register(VagaAgendaADEFAL)
class VagaAgendaADEFALAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "especialidade",
        "unidade",
        "profissional",
        "data",
        "horario",
        "disponivel",
    )
    list_filter = ("especialidade", "unidade", "disponivel", "data")  # type: ignore[assignment]
    search_fields = ("profissional", "especialidade")  # type: ignore[assignment]


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "protocolo",
        "paciente_pcd",
        "solicitado_por",
        "vaga",
        "status",
        "criado_em",
    )
    list_filter = ("status", "vaga__especialidade", "vaga__data")  # type: ignore[assignment]
    search_fields = (  # type: ignore[assignment]
        "protocolo",
        "paciente_pcd__cpf",
        "paciente_pcd__nome_completo",
    )
    readonly_fields = ("protocolo", "assinatura_qr", "criado_em", "atualizado_em")  # type: ignore[assignment]
    list_select_related = ("paciente_pcd", "solicitado_por", "vaga")  # type: ignore[assignment]


@admin.register(VagaFrotaAdaptada)
class VagaFrotaAdaptadaAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "veiculo_identificacao",
        "motorista",
        "data",
        "turno_horario",
        "vagas_cadeirante_total",
        "vagas_cadeirante_ocupadas",
    )
    list_filter = ("data", "veiculo_identificacao")  # type: ignore[assignment]
    search_fields = ("veiculo_identificacao", "motorista")  # type: ignore[assignment]


@admin.register(SolicitacaoTransporte)
class SolicitacaoTransporteAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "consulta",
        "frota",
        "equipamento_transporte",
        "precisa_acompanhante",
        "horario_apanhe_previsto",
        "status",
    )
    list_filter = ("status", "equipamento_transporte", "precisa_acompanhante")  # type: ignore[assignment]
    search_fields = ("consulta__protocolo", "endereco_embarque")  # type: ignore[assignment]
    list_select_related = ("consulta", "frota")  # type: ignore[assignment]

