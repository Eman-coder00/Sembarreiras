from django.contrib.auth.models import AbstractUser
from django.db import models


class PapelUsuario(models.TextChoices):
    PCD = "PCD", "Usuário PCD Física"
    CUIDADOR = "CUIDADOR", "Cuidador / Tutor Legal"


class StatusCadastro(models.IntegerChoices):
    ATIVO = 1, "Ativo"
    INATIVO = 2, "Inativo"
    BLOQUEADO = 3, "Bloqueado"


class Usuario(AbstractUser):
    cpf = models.CharField(max_length=14, unique=True)
    nome_completo = models.CharField(max_length=120)
    email = models.EmailField(max_length=200, unique=True)
    telefone = models.CharField(max_length=15)
    data_nascimento = models.DateField(null=True, blank=True)
    papel = models.CharField(
        max_length=12,
        choices=PapelUsuario.choices,
        default=PapelUsuario.PCD,
    )
    status_cadastro = models.IntegerField(
        choices=StatusCadastro.choices,
        default=StatusCadastro.ATIVO,
    )
    tentativas_login_falhas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)
    versao_sessao = models.PositiveIntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return f"{self.nome_completo or self.username} ({self.cpf})"
