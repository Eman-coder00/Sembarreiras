from typing import Any

from django.conf import settings
from django.db import models
from django.db.models import Q


class ParentescoContato(models.TextChoices):
    FAMILIAR = "FAMILIAR", "Familiar (Mãe/Pai/Filho/Cônjuge)"
    AMIGO = "AMIGO", "Amigo(a) de Confiança"
    CUIDADOR = "CUIDADOR", "Cuidador / Tutor Legal"
    VIZINHO = "VIZINHO", "Vizinho(a)"
    OUTRO = "OUTRO", "Outro"


class StatusContato(models.IntegerChoices):
    ATIVO = 1, "Ativo"
    INATIVO = 2, "Inativo"


class ContatoEmergencia(models.Model):
    objects: Any = models.Manager()

    titular_pcd = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contatos_emergencia",
        verbose_name="titular PCD",
    )
    nome = models.CharField("nome do contato", max_length=100)
    telefone = models.CharField("telefone", max_length=15)
    parentesco = models.CharField(
        "grau de relação",
        max_length=20,
        choices=ParentescoContato.choices,
        default=ParentescoContato.FAMILIAR,
    )
    prioridade = models.PositiveSmallIntegerField(
        "ordem de prioridade",
        default=1,
    )
    status = models.IntegerField(
        "status",
        choices=StatusContato.choices,
        default=StatusContato.ATIVO,
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)

    class Meta:
        verbose_name = "contato de emergência"
        verbose_name_plural = "contatos de emergência"
        ordering = ["prioridade", "id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(prioridade__gte=1, prioridade__lte=3),
                name="emergencia_contato_prioridade_1_a_3",
            ),
            models.UniqueConstraint(
                fields=["titular_pcd", "prioridade"],
                condition=Q(status=StatusContato.ATIVO),
                name="emergencia_prioridade_ativa_unica_por_titular",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.prioridade}º - {self.nome} ({self.telefone})"


class StatusOcorrenciaPanico(models.TextChoices):
    EM_CONTAGEM = "EM_CONTAGEM", "Em Contagem Regressiva (5s)"
    CANCELADO = "CANCELADO", "Cancelado pelo Usuário"
    ENTREGUE = "ENTREGUE", "Alerta Entregue (Push/SMS)"
    FALHA_PARCIAL = "FALHA_PARCIAL", "Falha Parcial de Entrega"
    FALLBACK_SMS = "FALLBACK_SMS", "Enviado via Fallback SMS Offline"


class OcorrenciaPanico(models.Model):
    objects: Any = models.Manager()

    codigo = models.CharField(
        "código da ocorrência",
        max_length=24,
        unique=True,
    )
    titular_pcd = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ocorrencias_panico",
        verbose_name="titular PCD",
    )
    latitude = models.FloatField("latitude", null=True, blank=True)
    longitude = models.FloatField("longitude", null=True, blank=True)
    endereco_aproximado = models.CharField(
        "endereço aproximado",
        max_length=200,
        blank=True,
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=StatusOcorrenciaPanico.choices,
        default=StatusOcorrenciaPanico.EM_CONTAGEM,
    )
    contatos_notificados = models.TextField(
        "contatos notificados",
        blank=True,
    )
    mensagem_enviada = models.TextField(
        "mensagem de emergência enviada",
        blank=True,
    )
    criado_em = models.DateTimeField("iniciado em", auto_now_add=True)
    finalizado_em = models.DateTimeField(
        "finalizado em",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "ocorrência de pânico"
        verbose_name_plural = "ocorrências de pânico"
        ordering = ["-criado_em", "-id"]

    def __str__(self) -> str:
        return f"{self.codigo} ({self.status})"

