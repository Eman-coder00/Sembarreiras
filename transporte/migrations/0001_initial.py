import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LinhaOnibus",
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
                        max_length=20, unique=True, verbose_name="código da linha"
                    ),
                ),
                ("nome", models.CharField(max_length=100, verbose_name="nome da linha")),
                (
                    "itinerario",
                    models.TextField(verbose_name="itinerário e bairros atendidos"),
                ),
                ("ativa", models.BooleanField(default=True, verbose_name="ativa")),
            ],
            options={
                "verbose_name": "linha de ônibus",
                "verbose_name_plural": "linhas de ônibus",
                "ordering": ["codigo"],
            },
        ),
        migrations.CreateModel(
            name="PontoParada",
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
                ("nome", models.CharField(max_length=100, verbose_name="nome do ponto")),
                (
                    "logradouro",
                    models.CharField(max_length=120, verbose_name="logradouro"),
                ),
                ("bairro", models.CharField(max_length=80, verbose_name="bairro")),
                ("latitude", models.FloatField(verbose_name="latitude")),
                ("longitude", models.FloatField(verbose_name="longitude")),
                (
                    "linhas",
                    models.ManyToManyField(
                        blank=True,
                        related_name="pontos_parada",
                        to="transporte.linhaonibus",
                        verbose_name="linhas atendidas",
                    ),
                ),
            ],
            options={
                "verbose_name": "ponto de parada",
                "verbose_name_plural": "pontos de parada",
                "ordering": ["bairro", "nome"],
            },
        ),
        migrations.CreateModel(
            name="VeiculoAdaptado",
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
                    "prefixo",
                    models.CharField(
                        max_length=20, unique=True, verbose_name="prefixo do veículo"
                    ),
                ),
                (
                    "acessibilidade_ativa",
                    models.BooleanField(
                        default=True, verbose_name="acessibilidade física funcional"
                    ),
                ),
                (
                    "tipo_equipamento",
                    models.CharField(
                        choices=[
                            (
                                "ELEVADOR_HIDRAULICO",
                                "Elevador Hidráulico Operacional",
                            ),
                            ("RAMPA_ACESSIVEL", "Rampa de Acesso Piso Baixo"),
                        ],
                        default="ELEVADOR_HIDRAULICO",
                        max_length=30,
                        verbose_name="equipamento de acessibilidade",
                    ),
                ),
                (
                    "vagas_cadeirante",
                    models.PositiveSmallIntegerField(
                        default=1, verbose_name="vagas para cadeirante"
                    ),
                ),
                ("latitude_atual", models.FloatField(verbose_name="latitude atual")),
                ("longitude_atual", models.FloatField(verbose_name="longitude atual")),
                (
                    "velocidade_media_kmh",
                    models.FloatField(
                        default=25.0, verbose_name="velocidade média (km/h)"
                    ),
                ),
                (
                    "atualizado_em",
                    models.DateTimeField(auto_now=True, verbose_name="atualizado em"),
                ),
                (
                    "linha",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="veiculos",
                        to="transporte.linhaonibus",
                        verbose_name="linha",
                    ),
                ),
            ],
            options={
                "verbose_name": "veículo adaptado",
                "verbose_name_plural": "veículos adaptados",
                "ordering": ["prefixo"],
            },
        ),
    ]

