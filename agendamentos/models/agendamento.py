from typing import Any

from django.conf import settings
from django.db import models


class EspecialidadeADEFAL(models.TextChoices):
    FISIOTERAPIA = "FISIOTERAPIA", "Fisioterapia Motora e Neurofuncional"
    ORTOPEDIA = "ORTOPEDIA", "Ortopedia e Traumatologia"
    TERAPIA_OCUPACIONAL = "TERAPIA_OCUPACIONAL", "Terapia Ocupacional"
    NEUROLOGIA = "NEUROLOGIA", "Neurologia Clínica"
    CONSULTA_GERAL = "CONSULTA_GERAL", "Consulta Médica Geral / Triagem ADEFAL"


class UnidadeADEFAL(models.TextChoices):
    SEDE_MACEIO = "SEDE_MACEIO", "Sede ADEFAL — Farol (Maceió/AL)"
    UNIDADE_REGIONAL = "UNIDADE_REGIONAL", "Unidade Regional de Reabilitação"


class StatusConsulta(models.IntegerChoices):
    CONFIRMADO = 1, "Confirmado"
    REALIZADO = 2, "Realizado"
    CANCELADO = 3, "Cancelado"
    REAGENDADO = 4, "Reagendado"


class EquipamentoTransporteHospitalar(models.TextChoices):
    CADEIRA_MANUAL = "CADEIRA_MANUAL", "Cadeira de Rodas Manual"
    CADEIRA_MOTORIZADA = "CADEIRA_MOTORIZADA", "Cadeira de Rodas Motorizada"
    MACA = "MACA", "Maca Hospitalar Adaptada"
    MULETAS = "MULETAS", "Muletas / Andador (Assento Preferencial)"


class StatusTransporteHospitalar(models.IntegerChoices):
    SOLICITADO = 1, "Solicitado"
    ROTA_CONFIRMADA = 2, "Rota Confirmada"
    A_CAMINHO = 3, "Veículo a Caminho"
    CONCLUIDO = 4, "Concluído"
    CANCELADO = 5, "Cancelado"


class VagaAgendaADEFAL(models.Model):
    objects: Any = models.Manager()

    especialidade = models.CharField(
        "especialidade",
        max_length=30,
        choices=EspecialidadeADEFAL.choices,
    )
    unidade = models.CharField(
        "unidade de atendimento",
        max_length=30,
        choices=UnidadeADEFAL.choices,
        default=UnidadeADEFAL.SEDE_MACEIO,
    )
    profissional = models.CharField("profissional responsável", max_length=100)
    data = models.DateField("data da consulta")
    horario = models.TimeField("horário")
    disponivel = models.BooleanField("disponível", default=True)

    class Meta:
        verbose_name = "vaga na agenda ADEFAL"
        verbose_name_plural = "vagas na agenda ADEFAL"
        ordering = ["data", "horario"]
        constraints = [
            models.UniqueConstraint(
                fields=["unidade", "profissional", "data", "horario"],
                name="agendamentos_vaga_unica_profissional_horario",
            )
        ]

    def __str__(self) -> str:
        return f"{self.especialidade} - {self.profissional} ({self.data} {self.horario})"


class Consulta(models.Model):
    objects: Any = models.Manager()

    protocolo = models.CharField(
        "protocolo de agendamento",
        max_length=24,
        unique=True,
    )
    paciente_pcd = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultas",
        verbose_name="paciente PCD",
    )
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consultas_solicitadas",
        verbose_name="solicitado por",
    )
    vaga = models.ForeignKey(
        VagaAgendaADEFAL,
        on_delete=models.PROTECT,
        related_name="agendamentos",
        verbose_name="vaga na agenda",
    )
    status = models.IntegerField(
        "status",
        choices=StatusConsulta.choices,
        default=StatusConsulta.CONFIRMADO,
    )
    justificativa_alteracao = models.CharField(
        "justificativa de cancelamento/remarcação",
        max_length=200,
        blank=True,
    )
    assinatura_qr = models.CharField(
        "assinatura criptográfica HMAC-SHA256",
        max_length=64,
    )
    criado_em = models.DateTimeField("criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "consulta ADEFAL"
        verbose_name_plural = "consultas ADEFAL"
        ordering = ["-vaga__data", "-vaga__horario", "-id"]

    def __str__(self) -> str:
        return f"{self.protocolo} - {self.paciente_pcd.cpf}"


class VagaFrotaAdaptada(models.Model):
    objects: Any = models.Manager()

    data = models.DateField("data da rota")
    turno_horario = models.TimeField("horário de referência")
    veiculo_identificacao = models.CharField(
        "identificação do veículo",
        max_length=60,
    )
    motorista = models.CharField("motorista", max_length=80)
    vagas_cadeirante_total = models.PositiveSmallIntegerField(
        "total de vagas para cadeirante",
        default=4,
    )
    vagas_cadeirante_ocupadas = models.PositiveSmallIntegerField(
        "vagas ocupadas",
        default=0,
    )

    class Meta:
        verbose_name = "frota adaptada ADEFAL"
        verbose_name_plural = "frota adaptada ADEFAL"
        ordering = ["data", "turno_horario"]

    @property
    def vagas_disponiveis(self) -> int:
        return max(
            0,
            int(self.vagas_cadeirante_total) - int(self.vagas_cadeirante_ocupadas),
        )

    def __str__(self) -> str:
        return f"{self.veiculo_identificacao} ({self.data} {self.turno_horario})"


class SolicitacaoTransporte(models.Model):
    objects: Any = models.Manager()

    consulta = models.OneToOneField(
        Consulta,
        on_delete=models.PROTECT,
        related_name="transporte",
        verbose_name="consulta vinculada",
    )
    frota = models.ForeignKey(
        VagaFrotaAdaptada,
        on_delete=models.PROTECT,
        related_name="reservas",
        verbose_name="veículo da frota adaptada",
    )
    endereco_embarque = models.CharField(
        "endereço de embarque porta a porta",
        max_length=250,
    )
    precisa_acompanhante = models.BooleanField(
        "necessita de acompanhante",
        default=False,
    )
    equipamento_transporte = models.CharField(
        "equipamento de locomoção",
        max_length=30,
        choices=EquipamentoTransporteHospitalar.choices,
        default=EquipamentoTransporteHospitalar.CADEIRA_MANUAL,
    )
    horario_apanhe_previsto = models.TimeField(
        "horário previsto de apanhe",
    )
    status = models.IntegerField(
        "status do transporte",
        choices=StatusTransporteHospitalar.choices,
        default=StatusTransporteHospitalar.ROTA_CONFIRMADA,
    )
    criado_em = models.DateTimeField("solicitado em", auto_now_add=True)

    class Meta:
        verbose_name = "solicitação de transporte hospitalar"
        verbose_name_plural = "solicitações de transporte hospitalar"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"Transporte {self.consulta.protocolo} ({self.frota.veiculo_identificacao})"

