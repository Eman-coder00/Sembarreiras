from typing import Any

from django.conf import settings
from django.db import models


class TipoDeficiencia(models.TextChoices):
    CADEIRANTE = "CADEIRANTE", "Cadeirante"
    MOBILIDADE_MEMBROS_INFERIORES = (
        "MOBILIDADE_MEMBROS_INFERIORES",
        "Mobilidade Reduzida nos Membros Inferiores",
    )
    LIMITACAO_MEMBROS_SUPERIORES = (
        "LIMITACAO_MEMBROS_SUPERIORES",
        "Limitação em Membros Superiores",
    )


class TamanhoToque(models.TextChoices):
    PADRAO = "PADRAO", "Padrão"
    EXPANDIDO = "EXPANDIDO", "Expandido"
    MAXIMO = "MAXIMO", "Máximo (48dp+)"


class TimeoutTela(models.TextChoices):
    PADRAO = "PADRAO", "Padrão"
    PROLONGADO_10M = "PROLONGADO_10M", "Prolongado (Até 10 minutos)"


class GrauParentescoVinculo(models.TextChoices):
    MAE_PAI = "MAE_PAI", "Mãe / Pai"
    TUTOR_LEGAL = "TUTOR_LEGAL", "Tutor Legal"
    CUIDADOR_PROFISSIONAL = "CUIDADOR_PROFISSIONAL", "Cuidador Profissional"
    CONJUGE = "CONJUGE", "Cônjuge"
    OUTRO = "OUTRO", "Outro"


class StatusVinculo(models.IntegerChoices):
    PENDENTE = 1, "Pendente"
    APROVADO = 2, "Aprovado"
    REVOGADO = 3, "Revogado"


class PerfilPCD(models.Model):
    objects: Any = models.Manager()

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="perfil_pcd",
    )
    tipo_deficiencia = models.CharField(
        max_length=40,
        choices=TipoDeficiencia.choices,
        default=TipoDeficiencia.CADEIRANTE,
    )
    equipamentos_apoio = models.CharField(
        max_length=200,
        default="CADEIRA_MANUAL",
    )
    tamanho_toque = models.CharField(
        max_length=20,
        choices=TamanhoToque.choices,
        default=TamanhoToque.PADRAO,
    )
    timeout_tela = models.CharField(
        max_length=20,
        choices=TimeoutTela.choices,
        default=TimeoutTela.PADRAO,
    )
    alto_contraste = models.BooleanField(default=False)
    cep = models.CharField(max_length=9)
    logradouro = models.CharField(max_length=100)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)

    class Meta:
        verbose_name = "Perfil PCD"
        verbose_name_plural = "Perfis PCD"

    def __str__(self) -> str:
        return f"Perfil PCD de {self.usuario}"


class VinculoCuidador(models.Model):
    objects: Any = models.Manager()

    cuidador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vinculos_como_cuidador",
    )
    titular_pcd = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="vinculos_cuidadores",
    )
    grau_parentesco = models.CharField(
        max_length=30,
        choices=GrauParentescoVinculo.choices,
    )
    codigo_otp = models.CharField(max_length=6)
    status = models.IntegerField(
        choices=StatusVinculo.choices,
        default=StatusVinculo.PENDENTE,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vínculo de Cuidador"
        verbose_name_plural = "Vínculos de Cuidadores"
        constraints = [
            models.UniqueConstraint(
                fields=["cuidador", "titular_pcd"],
                name="unico_vinculo_cuidador_titular",
            )
        ]

    def __str__(self) -> str:
        return f"{self.cuidador} -> {self.titular_pcd} ({StatusVinculo(int(str(self.status))).label})"


class TokenRecuperacaoSenha(models.Model):
    objects: Any = models.Manager()

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tokens_recuperacao",
    )
    codigo = models.CharField(max_length=6)
    expira_em = models.DateTimeField()
    utilizado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Token de Recuperação de Senha"
        verbose_name_plural = "Tokens de Recuperação de Senha"

    def __str__(self) -> str:
        return f"Token para {self.usuario} (utilizado={self.utilizado})"


class LogAuditoriaConta(models.Model):
    objects: Any = models.Manager()

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="logs_auditoria",
    )
    evento = models.CharField(max_length=60)
    detalhes = models.TextField(blank=True)
    ip = models.CharField(max_length=45, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoria de Conta"
        verbose_name_plural = "Logs de Auditoria de Contas"
        ordering = ["-criado_em"]

    def __str__(self) -> str:
        return f"{self.evento} - {self.usuario} ({self.criado_em})"


class CepLocal(models.Model):
    objects: Any = models.Manager()

    cep = models.CharField(max_length=9, unique=True)
    logradouro = models.CharField(max_length=100)
    bairro = models.CharField(max_length=100)
    municipio = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)

    class Meta:
        verbose_name = "CEP Local"
        verbose_name_plural = "CEPs Locais"

    def __str__(self) -> str:
        return f"{self.cep} - {self.logradouro}, {self.bairro}"

