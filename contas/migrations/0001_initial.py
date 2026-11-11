# Generated for Django 6.1.3

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CepLocal",
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
                ("cep", models.CharField(max_length=9, unique=True)),
                ("logradouro", models.CharField(max_length=100)),
                ("bairro", models.CharField(max_length=100)),
                ("municipio", models.CharField(max_length=100)),
                ("uf", models.CharField(max_length=2)),
            ],
            options={
                "verbose_name": "CEP Local",
                "verbose_name_plural": "CEPs Locais",
            },
        ),
        migrations.CreateModel(
            name="Usuario",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("cpf", models.CharField(max_length=14, unique=True)),
                ("nome_completo", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=200, unique=True)),
                ("telefone", models.CharField(max_length=15)),
                ("data_nascimento", models.DateField(blank=True, null=True)),
                (
                    "papel",
                    models.CharField(
                        choices=[
                            ("PCD", "Usuário PCD Física"),
                            ("CUIDADOR", "Cuidador / Tutor Legal"),
                        ],
                        default="PCD",
                        max_length=12,
                    ),
                ),
                (
                    "status_cadastro",
                    models.IntegerField(
                        choices=[(1, "Ativo"), (2, "Inativo"), (3, "Bloqueado")],
                        default=1,
                    ),
                ),
                (
                    "tentativas_login_falhas",
                    models.PositiveSmallIntegerField(default=0),
                ),
                ("bloqueado_ate", models.DateTimeField(blank=True, null=True)),
                ("versao_sessao", models.PositiveIntegerField(default=1)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Usuário",
                "verbose_name_plural": "Usuários",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="LogAuditoriaConta",
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
                ("evento", models.CharField(max_length=60)),
                ("detalhes", models.TextField(blank=True)),
                ("ip", models.CharField(blank=True, max_length=45)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="logs_auditoria",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Log de Auditoria de Conta",
                "verbose_name_plural": "Logs de Auditoria de Contas",
                "ordering": ["-criado_em"],
            },
        ),
        migrations.CreateModel(
            name="PerfilPCD",
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
                    "tipo_deficiencia",
                    models.CharField(
                        choices=[
                            ("CADEIRANTE", "Cadeirante"),
                            (
                                "MOBILIDADE_MEMBROS_INFERIORES",
                                "Mobilidade Reduzida nos Membros Inferiores",
                            ),
                            (
                                "LIMITACAO_MEMBROS_SUPERIORES",
                                "Limitação em Membros Superiores",
                            ),
                        ],
                        default="CADEIRANTE",
                        max_length=40,
                    ),
                ),
                (
                    "equipamentos_apoio",
                    models.CharField(default="CADEIRA_MANUAL", max_length=200),
                ),
                (
                    "tamanho_toque",
                    models.CharField(
                        choices=[
                            ("PADRAO", "Padrão"),
                            ("EXPANDIDO", "Expandido"),
                            ("MAXIMO", "Máximo (48dp+)"),
                        ],
                        default="PADRAO",
                        max_length=20,
                    ),
                ),
                (
                    "timeout_tela",
                    models.CharField(
                        choices=[
                            ("PADRAO", "Padrão"),
                            ("PROLONGADO_10M", "Prolongado (Até 10 minutos)"),
                        ],
                        default="PADRAO",
                        max_length=20,
                    ),
                ),
                ("alto_contraste", models.BooleanField(default=False)),
                ("cep", models.CharField(max_length=9)),
                ("logradouro", models.CharField(max_length=100)),
                ("numero", models.CharField(max_length=10)),
                ("complemento", models.CharField(blank=True, max_length=100)),
                ("bairro", models.CharField(max_length=100)),
                ("municipio", models.CharField(max_length=100)),
                ("uf", models.CharField(max_length=2)),
                (
                    "usuario",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="perfil_pcd",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil PCD",
                "verbose_name_plural": "Perfis PCD",
            },
        ),
        migrations.CreateModel(
            name="TokenRecuperacaoSenha",
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
                ("codigo", models.CharField(max_length=6)),
                ("expira_em", models.DateTimeField()),
                ("utilizado", models.BooleanField(default=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tokens_recuperacao",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Token de Recuperação de Senha",
                "verbose_name_plural": "Tokens de Recuperação de Senha",
            },
        ),
        migrations.CreateModel(
            name="VinculoCuidador",
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
                    "grau_parentesco",
                    models.CharField(
                        choices=[
                            ("MAE_PAI", "Mãe / Pai"),
                            ("TUTOR_LEGAL", "Tutor Legal"),
                            ("CUIDADOR_PROFISSIONAL", "Cuidador Profissional"),
                            ("CONJUGE", "Cônjuge"),
                            ("OUTRO", "Outro"),
                        ],
                        max_length=30,
                    ),
                ),
                ("codigo_otp", models.CharField(max_length=6)),
                (
                    "status",
                    models.IntegerField(
                        choices=[(1, "Pendente"), (2, "Aprovado"), (3, "Revogado")],
                        default=1,
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                (
                    "cuidador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vinculos_como_cuidador",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "titular_pcd",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="vinculos_cuidadores",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Vínculo de Cuidador",
                "verbose_name_plural": "Vínculos de Cuidadores",
                "constraints": [
                    models.UniqueConstraint(
                        fields=("cuidador", "titular_pcd"),
                        name="unico_vinculo_cuidador_titular",
                    )
                ],
            },
        ),
    ]
