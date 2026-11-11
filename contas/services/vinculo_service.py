import secrets
from typing import Any

from django.db import transaction
from django.db.models import Q, QuerySet

from contas.exceptions import (
    CpfJaCadastrado,
    EmailJaCadastrado,
    VinculoInvalido,
)
from contas.models import (
    LogAuditoriaConta,
    PapelUsuario,
    StatusCadastro,
    StatusVinculo,
    Usuario,
    VinculoCuidador,
)
from .conta_service import formatar_cpf


class VinculoCuidadorService:
    @staticmethod
    def cadastrar_cuidador_e_solicitar_vinculo(
        *,
        cpf_cuidador: str,
        nome_completo: str,
        email: str,
        telefone: str,
        senha: str,
        cpf_titular_pcd: str,
        grau_parentesco: str,
        ip: str = "",
    ) -> VinculoCuidador | Any:
        cpf_cuidador_norm = formatar_cpf(cpf_cuidador)
        cpf_titular_norm = formatar_cpf(cpf_titular_pcd)
        email_norm = email.strip().lower()

        if cpf_cuidador_norm == cpf_titular_norm:
            raise VinculoInvalido("O CPF do cuidador deve ser diferente do titular PCD.")

        titular = Usuario.objects.filter(
            cpf=cpf_titular_norm,
            papel=PapelUsuario.PCD,
            status_cadastro=StatusCadastro.ATIVO,
            is_active=True,
        ).first()
        if not titular:
            raise VinculoInvalido("Titular PCD não encontrado ou inativo.")

        if Usuario.objects.filter(cpf=cpf_cuidador_norm).exists():
            raise CpfJaCadastrado("CPF já cadastrado")
        if Usuario.objects.filter(email__iexact=email_norm).exists():
            raise EmailJaCadastrado("E-mail já cadastrado")

        codigo_otp = f"{secrets.randbelow(1_000_000):06d}"

        with transaction.atomic():
            cuidador = Usuario(
                username=cpf_cuidador_norm,
                cpf=cpf_cuidador_norm,
                nome_completo=nome_completo.strip(),
                email=email_norm,
                telefone=telefone.strip(),
                papel=PapelUsuario.CUIDADOR,
                status_cadastro=StatusCadastro.ATIVO,
                is_active=True,
            )
            cuidador.set_password(senha)
            cuidador.save()

            vinculo = VinculoCuidador.objects.create(
                cuidador=cuidador,
                titular_pcd=titular,
                grau_parentesco=grau_parentesco,
                codigo_otp=codigo_otp,
                status=StatusVinculo.PENDENTE,
            )

            LogAuditoriaConta.objects.create(
                usuario=titular,
                evento="VINCULO_SOLICITADO",
                detalhes=f"Solicitação de vínculo iniciada pelo cuidador {cuidador.cpf}.",
                ip=ip[:45],
            )
        return vinculo

    @staticmethod
    def confirmar_vinculo(
        *,
        vinculo_id: int,
        codigo_otp: str,
        solicitante: Any,
        ip: str = "",
    ) -> VinculoCuidador | Any:
        vinculo = (
            VinculoCuidador.objects.select_related("cuidador", "titular_pcd")
            .filter(
                Q(pk=vinculo_id),
                Q(titular_pcd=solicitante) | Q(cuidador=solicitante),
            )
            .first()
        )
        if not vinculo or vinculo.status != StatusVinculo.PENDENTE:
            raise VinculoInvalido("Solicitação de vínculo não encontrada ou já processada.")

        if not secrets.compare_digest(vinculo.codigo_otp, (codigo_otp or "").strip()):
            raise VinculoInvalido("Código OTP inválido.")

        with transaction.atomic():
            vinculo.status = StatusVinculo.APROVADO
            vinculo.save(update_fields=["status", "atualizado_em"])

            LogAuditoriaConta.objects.create(
                usuario=vinculo.titular_pcd,
                evento="VINCULO_APROVADO",
                detalhes=f"Vínculo com cuidador {vinculo.cuidador.cpf} aprovado via OTP.",
                ip=ip[:45],
            )
        return vinculo

    @staticmethod
    def revogar_vinculo(
        *,
        vinculo_id: int,
        solicitante: Any,
        ip: str = "",
    ) -> VinculoCuidador | Any:
        vinculo = (
            VinculoCuidador.objects.select_related("cuidador", "titular_pcd")
            .filter(
                Q(pk=vinculo_id),
                Q(titular_pcd=solicitante) | Q(cuidador=solicitante),
            )
            .first()
        )
        if not vinculo:
            raise VinculoInvalido("Vínculo não encontrado.")

        with transaction.atomic():
            vinculo.status = StatusVinculo.REVOGADO
            vinculo.save(update_fields=["status", "atualizado_em"])

            LogAuditoriaConta.objects.create(
                usuario=vinculo.titular_pcd,
                evento="VINCULO_REVOGADO",
                detalhes=f"Vínculo com cuidador {vinculo.cuidador.cpf} revogado por {solicitante.cpf}.",
                ip=ip[:45],
            )
        return vinculo

    @staticmethod
    def listar_vinculos(usuario: Any) -> QuerySet[Any]:
        if getattr(usuario, "papel", None) == PapelUsuario.PCD:
            return VinculoCuidador.objects.select_related("cuidador", "titular_pcd").filter(
                titular_pcd=usuario
            )
        return VinculoCuidador.objects.select_related("cuidador", "titular_pcd").filter(
            cuidador=usuario
        )

