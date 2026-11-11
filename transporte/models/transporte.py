from typing import Any

from django.db import models


class TipoEquipamentoOnibus(models.TextChoices):
    ELEVADOR_HIDRAULICO = "ELEVADOR_HIDRAULICO", "Elevador Hidráulico Operacional"
    RAMPA_ACESSIVEL = "RAMPA_ACESSIVEL", "Rampa de Acesso Piso Baixo"


class LinhaOnibus(models.Model):
    objects: Any = models.Manager()

    codigo = models.CharField("código da linha", max_length=20, unique=True)
    nome = models.CharField("nome da linha", max_length=100)
    itinerario = models.TextField("itinerário e bairros atendidos")
    ativa = models.BooleanField("ativa", default=True)

    class Meta:
        verbose_name = "linha de ônibus"
        verbose_name_plural = "linhas de ônibus"
        ordering = ["codigo"]

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


class PontoParada(models.Model):
    objects: Any = models.Manager()

    nome = models.CharField("nome do ponto", max_length=100)
    logradouro = models.CharField("logradouro", max_length=120)
    bairro = models.CharField("bairro", max_length=80)
    latitude = models.FloatField("latitude")
    longitude = models.FloatField("longitude")
    linhas = models.ManyToManyField(
        LinhaOnibus,
        related_name="pontos_parada",
        verbose_name="linhas atendidas",
        blank=True,
    )

    class Meta:
        verbose_name = "ponto de parada"
        verbose_name_plural = "pontos de parada"
        ordering = ["bairro", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.bairro})"


class VeiculoAdaptado(models.Model):
    objects: Any = models.Manager()

    prefixo = models.CharField("prefixo do veículo", max_length=20, unique=True)
    linha = models.ForeignKey(
        LinhaOnibus,
        on_delete=models.PROTECT,
        related_name="veiculos",
        verbose_name="linha",
    )
    acessibilidade_ativa = models.BooleanField(
        "acessibilidade física funcional",
        default=True,
    )
    tipo_equipamento = models.CharField(
        "equipamento de acessibilidade",
        max_length=30,
        choices=TipoEquipamentoOnibus.choices,
        default=TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
    )
    vagas_cadeirante = models.PositiveSmallIntegerField(
        "vagas para cadeirante",
        default=1,
    )
    latitude_atual = models.FloatField("latitude atual")
    longitude_atual = models.FloatField("longitude atual")
    velocidade_media_kmh = models.FloatField(
        "velocidade média (km/h)",
        default=25.0,
    )
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "veículo adaptado"
        verbose_name_plural = "veículos adaptados"
        ordering = ["prefixo"]

    def __str__(self) -> str:
        return f"{self.prefixo} ({self.linha.codigo})"

