import os
from typing import Any
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone


def caminho_laudo_seguro(instance: Any, filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    hoje = timezone.localdate()
    return f"laudos/{hoje.year:04d}/{hoje.month:02d}/{uuid4().hex}{ext}"


def caminho_comprovante_seguro(instance: Any, filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    hoje = timezone.localdate()
    return f"comprovantes/{hoje.year:04d}/{hoje.month:02d}/{uuid4().hex}{ext}"


class TipoEquipamentoApoio(models.TextChoices):
    CADEIRA_MANUAL = "CADEIRA_MANUAL", "Cadeira de Rodas Manual"
    CADEIRA_MOTORIZADA = "CADEIRA_MOTORIZADA", "Cadeira de Rodas Motorizada"
    CADEIRA_BANHO = "CADEIRA_BANHO", "Cadeira de Banho Higiênica"
    MULETA_BENGALA = "MULETA_BENGALA", "Par de Muletas Canadenses / Bengala"
    ANDADOR = "ANDADOR", "Andador Articulado de Alumínio"
    ORTESE_PROTESE = "ORTESE_PROTESE", "Órtese / Prótese Sob Medida"


class StatusSolicitacaoEquipamento(models.IntegerChoices):
    EM_ANALISE = 1, "Em Análise de Triagem Clínica"
    AGUARDANDO_ESTOQUE = 2, "Aguardando Disponibilidade no Almoxarifado"
    APROVADO_RETIRADA = 3, "Aprovado — Pronto para Retirada na ADEFAL"
    DEFERIDO_ENTREGUE = 4, "Deferido — Empréstimo Entregue / Vigente"
    INDEFERIDO = 5, "Indeferido (Ver Parecer Técnico)"


class AcaoDevolucaoEquipamento(models.TextChoices):
    NENHUMA = "NENHUMA", "Em Uso Normal"
    RENOVACAO_SOLICITADA = "RENOVACAO_SOLICITADA", "Renovação de Prazo Solicitada"
    DEVOLUCAO_CONFIRMADA = "DEVOLUCAO_CONFIRMADA", "Devolução e Vistoria Agendadas"


class SolicitacaoEquipamento(models.Model):
    objects: Any = models.Manager()

    protocolo = models.CharField(
        "protocolo da solicitação",
        max_length=24,
        unique=True,
    )
    beneficiario_pcd = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitacoes_equipamento",
        verbose_name="beneficiário PCD",
    )
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="equipamentos_requisitados",
        verbose_name="solicitado por",
    )
    tipo_equipamento = models.CharField(
        "tipo de equipamento",
        max_length=30,
        choices=TipoEquipamentoApoio.choices,
    )
    largura_quadril_cm = models.PositiveSmallIntegerField(
        "largura do quadril (cm)"
    )
    altura_cm = models.PositiveSmallIntegerField("estatura / altura (cm)")
    peso_kg = models.DecimalField(
        "peso corporal (kg)",
        max_digits=5,
        decimal_places=2,
    )
    observacoes_clinicas = models.TextField(
        "observações clínicas e ergonômicas",
        max_length=500,
        blank=True,
    )
    crm_medico = models.CharField(
        "CRM do médico emissor",
        max_length=30,
        blank=True,
    )
    data_emissao_laudo = models.DateField(
        "data de emissão do laudo",
        null=True,
        blank=True,
    )
    arquivo_laudo = models.FileField(
        "laudo médico (PDF/JPG/PNG até 10 MB)",
        upload_to=caminho_laudo_seguro,
    )
    arquivo_comprovante_residencia = models.FileField(
        "comprovante de residência (PDF/JPG/PNG até 5 MB)",
        upload_to=caminho_comprovante_seguro,
    )
    status = models.IntegerField(
        "status da solicitação",
        choices=StatusSolicitacaoEquipamento.choices,
        default=StatusSolicitacaoEquipamento.EM_ANALISE,
    )
    parecer_tecnico = models.TextField(
        "parecer técnico da ADEFAL",
        blank=True,
    )
    data_vencimento_emprestimo = models.DateField(
        "data de vencimento do empréstimo",
        null=True,
        blank=True,
    )
    acao_devolucao = models.CharField(
        "situação de renovação/devolução",
        max_length=30,
        choices=AcaoDevolucaoEquipamento.choices,
        default=AcaoDevolucaoEquipamento.NENHUMA,
    )
    justificativa_renovacao = models.TextField(
        "justificativa para renovação de prazo",
        blank=True,
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "solicitação de equipamento"
        verbose_name_plural = "solicitações de equipamentos"
        ordering = ["-criado_em", "-id"]

    def __str__(self) -> str:
        return f"{self.protocolo} - {self.tipo_equipamento}"


class EventoLinhaTempoEquipamento(models.Model):
    objects: Any = models.Manager()

    solicitacao = models.ForeignKey(
        SolicitacaoEquipamento,
        on_delete=models.PROTECT,
        related_name="eventos",
        verbose_name="solicitação",
    )
    status = models.IntegerField(
        "etapa registrada",
        choices=StatusSolicitacaoEquipamento.choices,
    )
    descricao = models.CharField("descrição da etapa", max_length=250)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="registrado por",
    )
    criado_em = models.DateTimeField("data e hora", auto_now_add=True)

    class Meta:
        verbose_name = "evento da linha do tempo"
        verbose_name_plural = "eventos da linha do tempo"
        ordering = ["criado_em", "id"]

    def __str__(self) -> str:
        return f"{self.solicitacao.protocolo} - {self.descricao}"

