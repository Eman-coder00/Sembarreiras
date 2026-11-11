import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VagaAgendaADEFAL",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "especialidade",
                    models.CharField(
                        choices=[
                            (
                                "FISIOTERAPIA",
                                "Fisioterapia Motora e Neurofuncional",
                            ),
                            ("ORTOPEDIA", "Ortopedia e Traumatologia"),
                            ("TERAPIA_OCUPACIONAL", "Terapia Ocupacional"),
                            ("NEUROLOGIA", "Neurologia Clínica"),
                            (
                                "CONSULTA_GERAL",
                                "Consulta Médica Geral / Triagem ADEFAL",
                            ),
                        ],
                        max_length=30,
                        verbose_name="especialidade",
                    ),
                ),
                (
                    "unidade",
                    models.CharField(
                        choices=[
                            ("SEDE_MACEIO", "Sede ADEFAL — Farol (Maceió/AL)"),
                            (
                                "UNIDADE_REGIONAL",
                                "Unidade Regional de Reabilitação",
                            ),
                        ],
                        default="SEDE_MACEIO",
                        max_length=30,
                        verbose_name="unidade de atendimento",
                    ),
                ),
                (
                    "profissional",
                    models.CharField(
                        max_length=100, verbose_name="profissional responsável"
                    ),
                ),
                ("data", models.DateField(verbose_name="data da consulta")),
                ("horario", models.TimeField(verbose_name="horário")),
                (
                    "disponivel",
                    models.BooleanField(default=True, verbose_name="disponível"),
                ),
            ],
            options={
                "verbose_name": "vaga na agenda ADEFAL",
                "verbose_name_plural": "vagas na agenda ADEFAL",
                "ordering": ["data", "horario"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("unidade", "profissional", "data", "horario"),
                        name="agendamentos_vaga_unica_profissional_horario",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="VagaFrotaAdaptada",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data", models.DateField(verbose_name="data da rota")),
                (
                    "turno_horario",
                    models.TimeField(verbose_name="horário de referência"),
                ),
                (
                    "veiculo_identificacao",
                    models.CharField(
                        max_length=60, verbose_name="identificação do veículo"
                    ),
                ),
                ("motorista", models.CharField(max_length=80, verbose_name="motorista")),
                (
                    "vagas_cadeirante_total",
                    models.PositiveSmallIntegerField(
                        default=4, verbose_name="total de vagas para cadeirante"
                    ),
                ),
                (
                    "vagas_cadeirante_ocupadas",
                    models.PositiveSmallIntegerField(
                        default=0, verbose_name="vagas ocupadas"
                    ),
                ),
            ],
            options={
                "verbose_name": "frota adaptada ADEFAL",
                "verbose_name_plural": "frota adaptada ADEFAL",
                "ordering": ["data", "turno_horario"],
            },
        ),
        migrations.CreateModel(
            name="Consulta",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "protocolo",
                    models.CharField(
                        max_length=24,
                        unique=True,
                        verbose_name="protocolo de agendamento",
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Confirmado"),
                            (2, "Realizado"),
                            (3, "Cancelado"),
                            (4, "Reagendado"),
                        ],
                        default=1,
                        verbose_name="status",
                    ),
                ),
                (
                    "justificativa_alteracao",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        verbose_name="justificativa de cancelamento/remarcação",
                    ),
                ),
                (
                    "assinatura_qr",
                    models.CharField(
                        max_length=64,
                        verbose_name="assinatura criptográfica HMAC-SHA256",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(auto_now=True, verbose_name="atualizado em"),
                ),
                (
                    "paciente_pcd",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="consultas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="paciente PCD",
                    ),
                ),
                (
                    "solicitado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="consultas_solicitadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="solicitado por",
                    ),
                ),
                (
                    "vaga",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="agendamentos",
                        to="agendamentos.vagaagendaadefal",
                        verbose_name="vaga na agenda",
                    ),
                ),
            ],
            options={
                "verbose_name": "consulta ADEFAL",
                "verbose_name_plural": "consultas ADEFAL",
                "ordering": ["-vaga__data", "-vaga__horario", "-id"],
            },
        ),
        migrations.CreateModel(
            name="SolicitacaoTransporte",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "endereco_embarque",
                    models.CharField(
                        max_length=250,
                        verbose_name="endereço de embarque porta a porta",
                    ),
                ),
                (
                    "precisa_acompanhante",
                    models.BooleanField(
                        default=False, verbose_name="necessita de acompanhante"
                    ),
                ),
                (
                    "equipamento_transporte",
                    models.CharField(
                        choices=[
                            ("CADEIRA_MANUAL", "Cadeira de Rodas Manual"),
                            ("CADEIRA_MOTORIZADA", "Cadeira de Rodas Motorizada"),
                            ("MACA", "Maca Hospitalar Adaptada"),
                            (
                                "MULETAS",
                                "Muletas / Andador (Assento Preferencial)",
                            ),
                        ],
                        default="CADEIRA_MANUAL",
                        max_length=30,
                        verbose_name="equipamento de locomoção",
                    ),
                ),
                (
                    "horario_apanhe_previsto",
                    models.TimeField(verbose_name="horário previsto de apanhe"),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Solicitado"),
                            (2, "Rota Confirmada"),
                            (3, "Veículo a Caminho"),
                            (4, "Concluído"),
                            (5, "Cancelado"),
                        ],
                        default=2,
                        verbose_name="status do transporte",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="solicitado em"),
                ),
                (
                    "consulta",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="transporte",
                        to="agendamentos.consulta",
                        verbose_name="consulta vinculada",
                    ),
                ),
                (
                    "frota",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reservas",
                        to="agendamentos.vagafrotaadaptada",
                        verbose_name="veículo da frota adaptada",
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitação de transporte hospitalar",
                "verbose_name_plural": "solicitações de transporte hospitalar",
                "ordering": ["-criado_em"],
            },
        ),
    ]

