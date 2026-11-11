from django.contrib import admin

from .models import LinhaOnibus, PontoParada, VeiculoAdaptado


@admin.register(LinhaOnibus)
class LinhaOnibusAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ativa")  # type: ignore[assignment]
    list_filter = ("ativa",)  # type: ignore[assignment]
    search_fields = ("codigo", "nome", "itinerario")  # type: ignore[assignment]


@admin.register(PontoParada)
class PontoParadaAdmin(admin.ModelAdmin):
    list_display = ("nome", "bairro", "logradouro", "latitude", "longitude")  # type: ignore[assignment]
    list_filter = ("bairro",)  # type: ignore[assignment]
    search_fields = ("nome", "bairro", "logradouro")  # type: ignore[assignment]


@admin.register(VeiculoAdaptado)
class VeiculoAdaptadoAdmin(admin.ModelAdmin):
    list_display = (  # type: ignore[assignment]
        "prefixo",
        "linha",
        "acessibilidade_ativa",
        "tipo_equipamento",
        "vagas_cadeirante",
        "velocidade_media_kmh",
        "atualizado_em",
    )
    list_filter = ("acessibilidade_ativa", "tipo_equipamento", "linha")  # type: ignore[assignment]
    search_fields = ("prefixo", "linha__codigo", "linha__nome")  # type: ignore[assignment]
    list_select_related = ("linha",)  # type: ignore[assignment]

