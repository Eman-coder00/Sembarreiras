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
            name="ContatoEmergencia",
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
                ("nome", models.CharField(max_length=100, verbose_name="nome do contato")),
                ("telefone", models.CharField(max_length=15, verbose_name="telefone")),
                (
                    "parentesco",
                    models.CharField(
                        choices=[
                            ("FAMILIAR", "Familiar (Mãe/Pai/Filho/Cônjuge)"),
                            ("AMIGO", "Amigo(a) de Confiança"),
                            ("CUIDADOR", "Cuidador / Tutor Legal"),
                            ("VIZINHO", "Vizinho(a)"),
                            ("OUTRO", "Outro"),
                        ],
                        default="FAMILIAR",
                        max_length=20,
                        verbose_name="grau de relação",
                    ),
                ),
                (
                    "prioridade",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="ordem de prioridade"
                    ),
                ),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Ativo"), (2, "Inativo")],
                        default=1,
                        verbose_name="status",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="criado em"),
                ),
                (
                    "titular_pcd",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contatos_emergencia",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="titular PCD",
                    ),
                ),
            ],
            options={
                "verbose_name": "contato de emergência",
                "verbose_name_plural": "contatos de emergência",
                "ordering": ["prioridade", "id"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("prioridade__gte", 1), ("prioridade__lte", 3)),
                        name="emergencia_contato_prioridade_1_a_3",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", 1)),
                        fields=("titular_pcd", "prioridade"),
                        name="emergencia_prioridade_ativa_unica_por_titular",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="OcorrenciaPanico",
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
                    "codigo",
                    models.CharField(
                        max_length=24, unique=True, verbose_name="código da ocorrência"
                    ),
                ),
                (
                    "latitude",
                    models.FloatField(blank=True, null=True, verbose_name="latitude"),
                ),
                (
                    "longitude",
                    models.FloatField(blank=True, null=True, verbose_name="longitude"),
                ),
                (
                    "endereco_aproximado",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="endereço aproximado"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("EM_CONTAGEM", "Em Contagem Regressiva (5s)"),
                            ("CANCELADO", "Cancelado pelo Usuário"),
                            ("ENTREGUE", "Alerta Entregue (Push/SMS)"),
                            ("FALHA_PARCIAL", "Falha Parcial de Entrega"),
                            ("FALLBACK_SMS", "Enviado via Fallback SMS Offline"),
                        ],
                        default="EM_CONTAGEM",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "contatos_notificados",
                    models.TextField(blank=True, verbose_name="contatos notificados"),
                ),
                (
                    "mensagem_enviada",
                    models.TextField(
                        blank=True, verbose_name="mensagem de emergência enviada"
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="iniciado em"),
                ),
                (
                    "finalizado_em",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="finalizado em"
                    ),
                ),
                (
                    "titular_pcd",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ocorrencias_panico",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="titular PCD",
                    ),
                ),
            ],
            options={
                "verbose_name": "ocorrência de pânico",
                "verbose_name_plural": "ocorrências de pânico",
                "ordering": ["-criado_em", "-id"],
            },
        ),
    ]

