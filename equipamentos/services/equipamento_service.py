import os
import secrets
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from django.db import models, transaction
from django.utils import timezone

from contas.exceptions import PermissaoNegadaTitular
from contas.services import ContaService
from equipamentos.exceptions import (
    AnexoInvalido,
    OperacaoEmprestimoInvalida,
    SolicitacaoEquipamentoNaoEncontrada,
)
from equipamentos.models import (
    AcaoDevolucaoEquipamento,
    EventoLinhaTempoEquipamento,
    SolicitacaoEquipamento,
    StatusSolicitacaoEquipamento,
)

ASSINATURAS_BINARIAS_POR_EXTENSAO = {
    ".pdf": (b"%PDF-",),
    ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
}

CONTENT_TYPE_POR_EXTENSAO = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def _gerar_protocolo_equipamento() -> str:
    hoje = timezone.localdate().strftime("%Y%m%d")
    for _ in range(10):
        sufixo = f"{secrets.randbelow(9000) + 1000}"
        protocolo = f"EQP-{hoje}-{sufixo}"
        if not SolicitacaoEquipamento.objects.filter(
            protocolo=protocolo
        ).exists():
            return protocolo
    return f"EQP-{hoje}-{secrets.token_hex(2).upper()}"


class EquipamentoService:
    @staticmethod
    def validar_arquivo_anexo(
        arquivo: Any,
        tamanho_max_mb: int,
    ) -> None:
        if not arquivo:
            raise AnexoInvalido("Arquivo obrigatório não enviado.")

        nome = getattr(arquivo, "name", "") or ""
        ext = os.path.splitext(nome)[1].lower()
        if ext not in ASSINATURAS_BINARIAS_POR_EXTENSAO:
            raise AnexoInvalido(
                "Formato inválido. Envie apenas arquivos PDF, JPG ou PNG."
            )

        limite_bytes = int(tamanho_max_mb) * 1024 * 1024
        tamanho = int(getattr(arquivo, "size", 0) or 0)
        if tamanho <= 0:
            raise AnexoInvalido("O arquivo enviado está vazio.")
        if tamanho > limite_bytes:
            raise AnexoInvalido(
                f"Arquivo excede o tamanho máximo permitido de {tamanho_max_mb} MB."
            )

        if hasattr(arquivo, "seek"):
            arquivo.seek(0)
        cabecalho = arquivo.read(16)
        if hasattr(arquivo, "seek"):
            arquivo.seek(0)

        assinaturas_validas = ASSINATURAS_BINARIAS_POR_EXTENSAO[ext]
        if not any(cabecalho.startswith(sig) for sig in assinaturas_validas):
            raise AnexoInvalido(
                "Assinatura binária do arquivo (magic bytes) incompatível com o formato declarado (RS008)."
            )

    @staticmethod
    def listar_solicitacoes_autorizadas(
        solicitante: Any,
        *,
        titular_cpf: str | None = None,
    ) -> models.QuerySet[Any]:
        try:
            beneficiario = ContaService.obter_titular_autorizado(
                solicitante, titular_cpf=titular_cpf
            )
        except PermissaoNegadaTitular as exc:
            raise SolicitacaoEquipamentoNaoEncontrada(str(exc)) from exc

        return (
            SolicitacaoEquipamento.objects.select_related(
                "beneficiario_pcd", "solicitado_por"
            )
            .filter(beneficiario_pcd=beneficiario)
            .order_by("-criado_em", "-id")
        )

    @staticmethod
    def criar_solicitacao(
        solicitante: Any,
        *,
        tipo_equipamento: str,
        largura_quadril_cm: int,
        altura_cm: int,
        peso_kg: Decimal | float | str,
        arquivo_laudo: Any,
        arquivo_comprovante_residencia: Any,
        observacoes_clinicas: str = "",
        crm_medico: str = "",
        data_emissao_laudo: date | None = None,
        titular_cpf: str | None = None,
    ) -> SolicitacaoEquipamento | Any:
        try:
            beneficiario = ContaService.obter_titular_autorizado(
                solicitante, titular_cpf=titular_cpf
            )
        except PermissaoNegadaTitular as exc:
            raise SolicitacaoEquipamentoNaoEncontrada(str(exc)) from exc

        EquipamentoService.validar_arquivo_anexo(
            arquivo_laudo, tamanho_max_mb=10
        )
        EquipamentoService.validar_arquivo_anexo(
            arquivo_comprovante_residencia, tamanho_max_mb=5
        )

        with transaction.atomic():
            protocolo = _gerar_protocolo_equipamento()
            solicitacao = SolicitacaoEquipamento.objects.create(
                protocolo=protocolo,
                beneficiario_pcd=beneficiario,
                solicitado_por=solicitante,
                tipo_equipamento=tipo_equipamento,
                largura_quadril_cm=int(largura_quadril_cm),
                altura_cm=int(altura_cm),
                peso_kg=Decimal(str(peso_kg)),
                observacoes_clinicas=(observacoes_clinicas or "").strip()[:500],
                crm_medico=(crm_medico or "").strip()[:30],
                data_emissao_laudo=data_emissao_laudo,
                arquivo_laudo=arquivo_laudo,
                arquivo_comprovante_residencia=arquivo_comprovante_residencia,
                status=StatusSolicitacaoEquipamento.EM_ANALISE,
            )

            EventoLinhaTempoEquipamento.objects.create(
                solicitacao=solicitacao,
                status=StatusSolicitacaoEquipamento.EM_ANALISE,
                descricao=(
                    "Solicitação protocolada com laudo médico e comprovante de residência validados."
                ),
                registrado_por=solicitante,
            )

        return solicitacao

    @staticmethod
    def obter_detalhe_e_linha_tempo(
        solicitante: Any,
        protocolo: str,
    ) -> tuple[SolicitacaoEquipamento | Any, models.QuerySet[Any]]:
        try:
            solicitacao = (
                SolicitacaoEquipamento.objects.select_related(
                    "beneficiario_pcd", "solicitado_por"
                )
                .get(protocolo=(protocolo or "").strip())
            )
        except SolicitacaoEquipamento.DoesNotExist as exc:
            raise SolicitacaoEquipamentoNaoEncontrada(
                "Solicitação de equipamento não encontrada."
            ) from exc

        if not getattr(solicitante, "is_staff", False):
            try:
                titular = ContaService.obter_titular_autorizado(
                    solicitante,
                    titular_cpf=solicitacao.beneficiario_pcd.cpf,
                )
            except PermissaoNegadaTitular as exc:
                raise SolicitacaoEquipamentoNaoEncontrada(str(exc)) from exc

            if titular.pk != solicitacao.beneficiario_pcd_id:
                raise SolicitacaoEquipamentoNaoEncontrada(
                    "Usuário sem permissão para acessar esta solicitação."
                )

        eventos = EventoLinhaTempoEquipamento.objects.select_related(
            "registrado_por"
        ).filter(solicitacao=solicitacao)
        return solicitacao, eventos

    @staticmethod
    def obter_anexo_protegido(
        solicitante: Any,
        protocolo: str,
        tipo_documento: str,
    ) -> tuple[Any, str, str]:
        solicitacao, _ = EquipamentoService.obter_detalhe_e_linha_tempo(
            solicitante, protocolo
        )
        if tipo_documento == "laudo":
            campo_arquivo = solicitacao.arquivo_laudo
            prefixo = f"laudo-{solicitacao.protocolo}"
        elif tipo_documento == "comprovante":
            campo_arquivo = solicitacao.arquivo_comprovante_residencia
            prefixo = f"comprovante-{solicitacao.protocolo}"
        else:
            raise SolicitacaoEquipamentoNaoEncontrada(
                "Tipo de documento inválido."
            )

        if not campo_arquivo:
            raise SolicitacaoEquipamentoNaoEncontrada(
                "Arquivo não encontrado."
            )

        ext = os.path.splitext(campo_arquivo.name)[1].lower()
        content_type = CONTENT_TYPE_POR_EXTENSAO.get(
            ext, "application/octet-stream"
        )
        nome_download = f"{prefixo}{ext}"
        return campo_arquivo, content_type, nome_download

    @staticmethod
    def atualizar_status_triagem(
        operador_staff: Any,
        protocolo: str,
        *,
        novo_status: int,
        parecer_tecnico: str = "",
        data_vencimento: date | None = None,
    ) -> SolicitacaoEquipamento | Any:
        if not getattr(operador_staff, "is_staff", False):
            raise SolicitacaoEquipamentoNaoEncontrada(
                "Apenas a equipe técnica da ADEFAL pode atualizar o status de triagem."
            )

        solicitacao, _ = EquipamentoService.obter_detalhe_e_linha_tempo(
            operador_staff, protocolo
        )

        with transaction.atomic():
            solicitacao.status = int(novo_status)
            if parecer_tecnico:
                solicitacao.parecer_tecnico = parecer_tecnico.strip()

            if (
                int(novo_status)
                == StatusSolicitacaoEquipamento.DEFERIDO_ENTREGUE
            ):
                solicitacao.data_vencimento_emprestimo = (
                    data_vencimento
                    or (timezone.localdate() + timedelta(days=90))
                )
            elif data_vencimento is not None:
                solicitacao.data_vencimento_emprestimo = data_vencimento

            solicitacao.save()

            rotulo_status = StatusSolicitacaoEquipamento(int(novo_status)).label
            detalhe_parecer = (
                f" — Parecer: {parecer_tecnico.strip()}"
                if parecer_tecnico.strip()
                else ""
            )
            EventoLinhaTempoEquipamento.objects.create(
                solicitacao=solicitacao,
                status=int(novo_status),
                descricao=f"Triagem ADEFAL: {rotulo_status}{detalhe_parecer}"[:250],
                registrado_por=operador_staff,
            )

        return solicitacao

    @staticmethod
    def listar_alertas_vencimento(
        beneficiario_pcd: Any,
        data_referencia: date | None = None,
    ) -> list[dict[str, Any]]:
        ref = data_referencia or timezone.localdate()
        limite_7_dias = ref + timedelta(days=7)

        emprestimos = SolicitacaoEquipamento.objects.filter(
            beneficiario_pcd=beneficiario_pcd,
            status=StatusSolicitacaoEquipamento.DEFERIDO_ENTREGUE,
            data_vencimento_emprestimo__isnull=False,
            data_vencimento_emprestimo__lte=limite_7_dias,
        ).order_by("data_vencimento_emprestimo")

        alertas: list[dict[str, Any]] = []
        for item in emprestimos:
            dias_restantes = (item.data_vencimento_emprestimo - ref).days
            if dias_restantes <= 2:
                nivel = "URGENTE_2_DIAS"
                mensagem = (
                    f"Atenção urgente: faltam {max(0, dias_restantes)} dia(s) para o vencimento "
                    f"do empréstimo ({item.protocolo}). Confirme a devolução ou solicite renovação."
                )
            else:
                nivel = "AVISO_7_DIAS"
                mensagem = (
                    f"Aviso preventivo: faltam {dias_restantes} dias para o vencimento "
                    f"do empréstimo ({item.protocolo})."
                )
            alertas.append(
                {
                    "solicitacao": item,
                    "dias_restantes": dias_restantes,
                    "nivel": nivel,
                    "mensagem": mensagem,
                }
            )
        return alertas

    @staticmethod
    def registrar_renovacao_ou_devolucao(
        solicitante: Any,
        protocolo: str,
        *,
        acao: str,
        justificativa: str = "",
    ) -> SolicitacaoEquipamento | Any:
        solicitacao, _ = EquipamentoService.obter_detalhe_e_linha_tempo(
            solicitante, protocolo
        )
        if (
            solicitacao.status
            != StatusSolicitacaoEquipamento.DEFERIDO_ENTREGUE
        ):
            raise OperacaoEmprestimoInvalida(
                "Apenas equipamentos entregues em empréstimo vigente permitem renovação ou devolução."
            )

        justificativa_limpa = (justificativa or "").strip()
        if (
            acao == AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA
            and len(justificativa_limpa) < 5
        ):
            raise OperacaoEmprestimoInvalida(
                "Informe a justificativa clínica para solicitar a renovação do empréstimo."
            )

        if acao not in (
            AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA,
            AcaoDevolucaoEquipamento.DEVOLUCAO_CONFIRMADA,
        ):
            raise OperacaoEmprestimoInvalida("Ação de prazo inválida.")

        with transaction.atomic():
            solicitacao.acao_devolucao = acao
            if justificativa_limpa:
                solicitacao.justificativa_renovacao = justificativa_limpa
            solicitacao.save(
                update_fields=[
                    "acao_devolucao",
                    "justificativa_renovacao",
                    "atualizado_em",
                ]
            )

            descricao_evento = (
                f"Pedido de renovação de prazo enviado: {justificativa_limpa}"
                if acao == AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA
                else "Devolução e vistoria agendadas no almoxarifado da ADEFAL."
            )
            EventoLinhaTempoEquipamento.objects.create(
                solicitacao=solicitacao,
                status=solicitacao.status,
                descricao=descricao_evento[:250],
                registrado_por=solicitante,
            )

        return solicitacao

