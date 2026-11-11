import secrets
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from contas.exceptions import (
    ContaTemporariamenteBloqueada,
    CredenciaisInvalidas,
    TokenRecuperacaoInvalido,
)
from contas.models import (
    LogAuditoriaConta,
    StatusCadastro,
    TokenRecuperacaoSenha,
    Usuario,
)
from .conta_service import formatar_cpf

LIMITE_TENTATIVAS_LOGIN = 5
MINUTOS_BLOQUEIO_LOGIN = 15
MINUTOS_EXPIRACAO_TOKEN = 15


class AutenticacaoService:
    @staticmethod
    def _buscar_usuario_por_identificador(identificador: str) -> Usuario | Any:
        termo = (identificador or "").strip()
        if not termo:
            return None
        cpf_norm = formatar_cpf(termo)
        return Usuario.objects.filter(
            Q(cpf=cpf_norm) | Q(email__iexact=termo)
        ).first()

    @staticmethod
    def autenticar(
        *,
        identificador: str,
        senha: str,
        perfil_selecionado: str,
        ip: str = "",
    ) -> Usuario | Any:
        usuario = AutenticacaoService._buscar_usuario_por_identificador(identificador)
        if not usuario or usuario.status_cadastro == StatusCadastro.INATIVO or not usuario.is_active:
            raise CredenciaisInvalidas("Credenciais inválidas")

        agora = timezone.now()
        if usuario.status_cadastro == StatusCadastro.BLOQUEADO:
            raise ContaTemporariamenteBloqueada("Conta temporariamente bloqueada")

        if usuario.bloqueado_ate and usuario.bloqueado_ate > agora:
            raise ContaTemporariamenteBloqueada("Conta temporariamente bloqueada")

        if not usuario.check_password(senha):
            usuario.tentativas_login_falhas += 1
            if usuario.tentativas_login_falhas >= LIMITE_TENTATIVAS_LOGIN:
                usuario.bloqueado_ate = agora + timedelta(minutes=MINUTOS_BLOQUEIO_LOGIN)
                usuario.save(update_fields=["tentativas_login_falhas", "bloqueado_ate"])
                LogAuditoriaConta.objects.create(
                    usuario=usuario,
                    evento="CONTA_BLOQUEADA_TENTATIVAS",
                    detalhes="Conta bloqueada por 15 minutos após 5 falhas consecutivas.",
                    ip=ip[:45],
                )
                raise ContaTemporariamenteBloqueada("Conta temporariamente bloqueada")

            usuario.save(update_fields=["tentativas_login_falhas"])
            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="LOGIN_FALHA",
                detalhes=f"Tentativa inválida ({usuario.tentativas_login_falhas}/{LIMITE_TENTATIVAS_LOGIN}).",
                ip=ip[:45],
            )
            raise CredenciaisInvalidas("Credenciais inválidas")

        if usuario.papel != perfil_selecionado:
            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="LOGIN_FALHA_PERFIL",
                detalhes=f"Perfil selecionado ({perfil_selecionado}) diverge do cadastro ({usuario.papel}).",
                ip=ip[:45],
            )
            raise CredenciaisInvalidas("Credenciais inválidas")

        usuario.tentativas_login_falhas = 0
        usuario.bloqueado_ate = None
        usuario.save(update_fields=["tentativas_login_falhas", "bloqueado_ate"])

        LogAuditoriaConta.objects.create(
            usuario=usuario,
            evento="LOGIN_SUCESSO",
            detalhes=f"Acesso autenticado com perfil {perfil_selecionado}.",
            ip=ip[:45],
        )
        return usuario

    @staticmethod
    def solicitar_recuperacao_senha(
        *,
        identificador: str,
        ip: str = "",
    ) -> TokenRecuperacaoSenha | Any:
        usuario = AutenticacaoService._buscar_usuario_por_identificador(identificador)
        if not usuario or not usuario.is_active or usuario.status_cadastro != StatusCadastro.ATIVO:
            return None

        codigo = f"{secrets.randbelow(1_000_000):06d}"
        expira_em = timezone.now() + timedelta(minutes=MINUTOS_EXPIRACAO_TOKEN)

        with transaction.atomic():
            TokenRecuperacaoSenha.objects.filter(
                usuario=usuario, utilizado=False
            ).update(utilizado=True)
            token = TokenRecuperacaoSenha.objects.create(
                usuario=usuario,
                codigo=codigo,
                expira_em=expira_em,
            )
            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="SOLICITACAO_RECUPERACAO_SENHA",
                detalhes="Token temporário de 6 dígitos emitido (validade de 15 minutos).",
                ip=ip[:45],
            )
        return token

    @staticmethod
    def redefinir_senha(
        *,
        identificador: str,
        codigo: str,
        nova_senha: str,
        ip: str = "",
    ) -> Usuario | Any:
        usuario = AutenticacaoService._buscar_usuario_por_identificador(identificador)
        if not usuario or not usuario.is_active or usuario.status_cadastro != StatusCadastro.ATIVO:
            raise TokenRecuperacaoInvalido("Código de recuperação inválido ou expirado.")

        agora = timezone.now()
        token = (
            TokenRecuperacaoSenha.objects.filter(
                usuario=usuario,
                utilizado=False,
            )
            .order_by("-criado_em")
            .first()
        )
        if (
            not token
            or token.expira_em < agora
            or not secrets.compare_digest(token.codigo, (codigo or "").strip())
        ):
            raise TokenRecuperacaoInvalido("Código de recuperação inválido ou expirado.")

        with transaction.atomic():
            token.utilizado = True
            token.save(update_fields=["utilizado"])

            usuario.set_password(nova_senha)
            usuario.versao_sessao += 1
            usuario.tentativas_login_falhas = 0
            usuario.bloqueado_ate = None
            usuario.save()

            LogAuditoriaConta.objects.create(
                usuario=usuario,
                evento="REDEFINICAO_SENHA",
                detalhes="Senha redefinida com invalidação de sessões anteriores.",
                ip=ip[:45],
            )
        return usuario

