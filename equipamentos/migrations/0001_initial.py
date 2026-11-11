import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import equipamentos.models.equipamento


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SolicitacaoEquipamento",
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
                        verbose_name="protocolo da solicitação",
                    ),
                ),
                (
                    "tipo_equipamento",
                    models.CharField(
                        choices=[
                            ("CADEIRA_MANUAL", "Cadeira de Rodas Manual"),
                            (
                                "CADEIRA_MOTORIZADA",
                                "Cadeira de Rodas Motorizada",
                            ),
                            ("CADEIRA_BANHO", "Cadeira de Banho Higiênica"),
                            (
                                "MULETA_BENGALA",
                                "Par de Muletas Canadenses / Bengala",
                            ),
                            ("ANDADOR", "Andador Articulado de Alumínio"),
                            (
                                "ORTESE_PROTESE",
                                "Órtese / Prótese Sob Medida",
                            ),
                        ],
                        max_length=30,
                        verbose_name="tipo de equipamento",
                    ),
                ),
                (
                    "largura_quadril_cm",
                    models.PositiveSmallIntegerField(
                        verbose_name="largura do quadril (cm)"
                    ),
                ),
                (
                    "altura_cm",
                    models.PositiveSmallIntegerField(
                        verbose_name="estatura / altura (cm)"
                    ),
                ),
                (
                    "peso_kg",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        verbose_name="peso corporal (kg)",
                    ),
                ),
                (
                    "observacoes_clinicas",
                    models.TextField(
                        blank=True,
                        max_length=500,
                        verbose_name="observações clínicas e ergonômicas",
                    ),
                ),
                (
                    "crm_medico",
                    models.CharField(
                        blank=True,
                        max_length=30,
                        verbose_name="CRM do médico emissor",
                    ),
                ),
                (
                    "data_emissao_laudo",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="data de emissão do laudo",
                    ),
                ),
                (
                    "arquivo_laudo",
                    models.FileField(
                        upload_to=equipamentos.models.equipamento.caminho_laudo_seguro,
                        verbose_name="laudo médico (PDF/JPG/PNG até 10 MB)",
                    ),
                ),
                (
                    "arquivo_comprovante_residencia",
                    models.FileField(
                        upload_to=equipamentos.models.equipamento.caminho_comprovante_seguro,
                        verbose_name="comprovante de residência (PDF/JPG/PNG até 5 MB)",
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Em Análise de Triagem Clínica"),
                            (2, "Aguardando Disponibilidade no Almoxarifado"),
                            (3, "Aprovado — Pronto para Retirada na ADEFAL"),
                            (4, "Deferido — Empréstimo Entregue / Vigente"),
                            (5, "Indeferido (Ver Parecer Técnico)"),
                        ],
                        default=1,
                        verbose_name="status da solicitação",
                    ),
                ),
                (
                    "parecer_tecnico",
                    models.TextField(
                        blank=True, verbose_name="parecer técnico da ADEFAL"
                    ),
                ),
                (
                    "data_vencimento_emprestimo",
                    models.DateField(
                        blank=True,
                        null=True,
                        verbose_name="data de vencimento do empréstimo",
                    ),
                ),
                (
                    "acao_devolucao",
                    models.CharField(
                        choices=[
                            ("NENHUMA", "Em Uso Normal"),
                            (
                                "RENOVACAO_SOLICITADA",
                                "Renovação de Prazo Solicitada",
                            ),
                            (
                                "DEVOLUCAO_CONFIRMADA",
                                "Devolução e Vistoria Agendadas",
                            ),
                        ],
                        default="NENHUMA",
                        max_length=30,
                        verbose_name="situação de renovação/devolução",
                    ),
                ),
                (
                    "justificativa_renovacao",
                    models.TextField(
                        blank=True,
                        verbose_name="justificativa para renovação de prazo",
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
                    "beneficiario_pcd",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="solicitacoes_equipamento",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="beneficiário PCD",
                    ),
                ),
                (
                    "solicitado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipamentos_requisitados",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="solicitado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitação de equipamento",
                "verbose_name_plural": "solicitações de equipamentos",
                "ordering": ["-criado_em", "-id"],
            },
        ),
        migrations.CreateModel(
            name="EventoLinhaTempoEquipamento",
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
                    "status",
                    models.IntegerField(
                        choices=[
                            (1, "Em Análise de Triagem Clínica"),
                            (2, "Aguardando Disponibilidade no Almoxarifado"),
                            (3, "Aprovado — Pronto para Retirada na ADEFAL"),
                            (4, "Deferido — Empréstimo Entregue / Vigente"),
                            (5, "Indeferido (Ver Parecer Técnico)"),
                        ],
                        verbose_name="etapa registrada",
                    ),
                ),
                (
                    "descricao",
                    models.CharField(
                        max_length=250, verbose_name="descrição da etapa"
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="data e hora"),
                ),
                (
                    "registrado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="registrado por",
                    ),
                ),
                (
                    "solicitacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos",
                        to="equipamentos.solicitacaoequipamento",
                        verbose_name="solicitação",
                    ),
                ),
            ],
            options={
                "verbose_name": "evento da linha do tempo",
                "verbose_name_plural": "eventos da linha do tempo",
                "ordering": ["criado_em", "id"],
            },
        ),
    ]

