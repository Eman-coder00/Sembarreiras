import json
import secrets
from datetime import date
from typing import Any

from django.db import models, transaction
from django.utils import timezone

from contas.exceptions import PermissaoNegadaTitular
from contas.services import ContaService
from emergencia.exceptions import (
    JanelaCancelamentoEncerrada,
    LimiteContatosExcedido,
    MinimoContatoAtivoObrigatorio,
    OcorrenciaNaoEncontrada,
    SemContatosDeEmergencia,
)
from emergencia.models import (
    ContatoEmergencia,
    OcorrenciaPanico,
    StatusContato,
    StatusOcorrenciaPanico,
)


def _geocodificar_local(latitude: float, longitude: float) -> str:
    if -9.70 <= latitude <= -9.50 and -35.80 <= longitude <= -35.65:
        return (
            f"Região Metropolitana de Maceió/AL — Farol/Trapiche "
            f"({latitude:.5f}, {longitude:.5f})"
        )
    return f"Coordenadas GPS ({latitude:.5f}, {longitude:.5f}) — Alagoas/BR"


def _gerar_codigo_ocorrencia() -> str:
    hoje = timezone.localdate().strftime("%Y%m%d")
    for _ in range(10):
        sufixo = f"{secrets.randbelow(9000) + 1000}"
        codigo = f"PAN-{hoje}-{sufixo}"
        if not OcorrenciaPanico.objects.filter(codigo=codigo).exists():
            return codigo
    return f"PAN-{hoje}-{secrets.token_hex(2).upper()}"


class ContatoEmergenciaService:
    MAX_CONTATOS_ATIVOS = 3

    @staticmethod
    def listar_ativos(titular_pcd: Any) -> models.QuerySet[Any]:
        return ContatoEmergencia.objects.filter(
            titular_pcd=titular_pcd,
            status=StatusContato.ATIVO,
        ).order_by("prioridade", "id")

    @staticmethod
    def listar_json_sincronizacao(titular_pcd: Any) -> str:
        contatos = ContatoEmergenciaService.listar_ativos(titular_pcd)
        payload = [
            {
                "prioridade": c.prioridade,
                "nome": c.nome,
                "telefone": c.telefone,
                "parentesco": c.parentesco,
            }
            for c in contatos
        ]
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def obter_do_titular(
        contato_id: int,
        titular_pcd: Any,
    ) -> ContatoEmergencia | Any:
        try:
            return ContatoEmergencia.objects.get(
                pk=contato_id,
                titular_pcd=titular_pcd,
            )
        except ContatoEmergencia.DoesNotExist as exc:
            raise OcorrenciaNaoEncontrada(
                "Contato de emergência não encontrado."
            ) from exc

    @staticmethod
    def criar(
        *,
        titular_pcd: Any,
        nome: str,
        telefone: str,
        parentesco: str,
        prioridade: int,
    ) -> ContatoEmergencia | Any:
        ativos = ContatoEmergencia.objects.filter(
            titular_pcd=titular_pcd,
            status=StatusContato.ATIVO,
        )
        if ativos.count() >= ContatoEmergenciaService.MAX_CONTATOS_ATIVOS:
            raise LimiteContatosExcedido(
                "Limite máximo de 3 contatos de emergência ativos atingido."
            )
        if ativos.filter(prioridade=prioridade).exists():
            raise LimiteContatosExcedido(
                f"A {prioridade}ª prioridade já está ocupada por outro contato ativo."
            )

        with transaction.atomic():
            return ContatoEmergencia.objects.create(
                titular_pcd=titular_pcd,
                nome=nome.strip(),
                telefone=telefone.strip(),
                parentesco=parentesco,
                prioridade=int(prioridade),
                status=StatusContato.ATIVO,
            )

    @staticmethod
    def atualizar(
        contato_id: int,
        titular_pcd: Any,
        *,
        nome: str,
        telefone: str,
        parentesco: str,
        prioridade: int,
        status: int = StatusContato.ATIVO,
    ) -> ContatoEmergencia | Any:
        contato = ContatoEmergenciaService.obter_do_titular(
            contato_id, titular_pcd
        )
        outros_ativos = ContatoEmergencia.objects.filter(
            titular_pcd=titular_pcd,
            status=StatusContato.ATIVO,
        ).exclude(pk=contato.pk)

        if int(status) == StatusContato.INATIVO and not outros_ativos.exists():
            raise MinimoContatoAtivoObrigatorio(
                "É obrigatório manter ao menos 1 contato de emergência ativo."
            )

        if int(status) == StatusContato.ATIVO:
            if outros_ativos.count() >= ContatoEmergenciaService.MAX_CONTATOS_ATIVOS:
                raise LimiteContatosExcedido(
                    "Limite máximo de 3 contatos de emergência ativos atingido."
                )
            if outros_ativos.filter(prioridade=int(prioridade)).exists():
                raise LimiteContatosExcedido(
                    f"A {prioridade}ª prioridade já está ocupada por outro contato ativo."
                )

        with transaction.atomic():
            contato.nome = nome.strip()
            contato.telefone = telefone.strip()
            contato.parentesco = parentesco
            contato.prioridade = int(prioridade)
            contato.status = int(status)
            contato.save()
        return contato

    @staticmethod
    def excluir(contato_id: int, titular_pcd: Any) -> None:
        contato = ContatoEmergenciaService.obter_do_titular(
            contato_id, titular_pcd
        )
        outros_ativos = ContatoEmergencia.objects.filter(
            titular_pcd=titular_pcd,
            status=StatusContato.ATIVO,
        ).exclude(pk=contato.pk)

        if contato.status == StatusContato.ATIVO and not outros_ativos.exists():
            raise MinimoContatoAtivoObrigatorio(
                "É obrigatório manter ao menos 1 contato de emergência ativo."
            )

        with transaction.atomic():
            contato.delete()


class PanicoService:
    LATITUDE_PADRAO_MACEIO = -9.64985
    LONGITUDE_PADRAO_MACEIO = -35.70895

    @staticmethod
    def iniciar_acionamento(
        titular_pcd: Any,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> OcorrenciaPanico | Any:
        contatos = ContatoEmergenciaService.listar_ativos(titular_pcd)
        if not contatos.exists():
            raise SemContatosDeEmergencia(
                "Cadastre ao menos 1 contato de emergência ativo antes de acionar o botão de pânico."
            )

        lat = (
            float(latitude)
            if latitude is not None
            else PanicoService.LATITUDE_PADRAO_MACEIO
        )
        lng = (
            float(longitude)
            if longitude is not None
            else PanicoService.LONGITUDE_PADRAO_MACEIO
        )

        with transaction.atomic():
            return OcorrenciaPanico.objects.create(
                codigo=_gerar_codigo_ocorrencia(),
                titular_pcd=titular_pcd,
                latitude=lat,
                longitude=lng,
                endereco_aproximado=_geocodificar_local(lat, lng),
                status=StatusOcorrenciaPanico.EM_CONTAGEM,
            )

    @staticmethod
    def obter_ocorrencia_do_titular(
        ocorrencia_id: int,
        titular_pcd: Any,
    ) -> OcorrenciaPanico | Any:
        try:
            return OcorrenciaPanico.objects.select_related("titular_pcd").get(
                pk=ocorrencia_id,
                titular_pcd=titular_pcd,
            )
        except OcorrenciaPanico.DoesNotExist as exc:
            raise OcorrenciaNaoEncontrada(
                "Ocorrência de pânico não encontrada."
            ) from exc

    @staticmethod
    def cancelar_alerta(
        ocorrencia_id: int,
        titular_pcd: Any,
    ) -> OcorrenciaPanico | Any:
        ocorrencia = PanicoService.obter_ocorrencia_do_titular(
            ocorrencia_id, titular_pcd
        )
        if ocorrencia.status != StatusOcorrenciaPanico.EM_CONTAGEM:
            raise JanelaCancelamentoEncerrada(
                "A janela de cancelamento de 5 segundos já foi encerrada."
            )

        with transaction.atomic():
            ocorrencia.status = StatusOcorrenciaPanico.CANCELADO
            ocorrencia.finalizado_em = timezone.now()
            ocorrencia.contatos_notificados = ""
            ocorrencia.mensagem_enviada = ""
            ocorrencia.save()
        return ocorrencia

    @staticmethod
    def confirmar_disparo(
        ocorrencia_id: int,
        titular_pcd: Any,
        latitude: float | None = None,
        longitude: float | None = None,
        falha_dados: bool = False,
    ) -> OcorrenciaPanico | Any:
        ocorrencia = PanicoService.obter_ocorrencia_do_titular(
            ocorrencia_id, titular_pcd
        )
        if ocorrencia.status == StatusOcorrenciaPanico.CANCELADO:
            raise JanelaCancelamentoEncerrada(
                "Esta ocorrência já foi cancelada pelo usuário."
            )

        contatos = list(ContatoEmergenciaService.listar_ativos(titular_pcd))
        if not contatos:
            raise SemContatosDeEmergencia(
                "Nenhum contato de emergência ativo encontrado para o disparo."
            )

        lat = (
            float(latitude)
            if latitude is not None
            else (
                ocorrencia.latitude
                if ocorrencia.latitude is not None
                else PanicoService.LATITUDE_PADRAO_MACEIO
            )
        )
        lng = (
            float(longitude)
            if longitude is not None
            else (
                ocorrencia.longitude
                if ocorrencia.longitude is not None
                else PanicoService.LONGITUDE_PADRAO_MACEIO
            )
        )

        link_mapa = f"https://maps.google.com/?q={lat:.5f},{lng:.5f}"
        mensagem_padrao = (
            f"EMERGÊNCIA! Preciso de ajuda imediata. "
            f"Titular: {titular_pcd.nome_completo}. "
            f"Minha localização atual é: {link_mapa}"
        )
        resumo_contatos = ", ".join(
            f"{c.prioridade}º {c.nome} ({c.telefone})" for c in contatos
        )

        status_final = (
            StatusOcorrenciaPanico.FALLBACK_SMS
            if falha_dados
            else StatusOcorrenciaPanico.ENTREGUE
        )

        with transaction.atomic():
            ocorrencia.latitude = lat
            ocorrencia.longitude = lng
            ocorrencia.endereco_aproximado = _geocodificar_local(lat, lng)
            ocorrencia.status = status_final
            ocorrencia.contatos_notificados = resumo_contatos
            ocorrencia.mensagem_enviada = mensagem_padrao
            ocorrencia.finalizado_em = timezone.now()
            ocorrencia.save()

        return ocorrencia

    @staticmethod
    def listar_historico(
        solicitante: Any,
        *,
        titular_cpf: str | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        status: str | None = None,
    ) -> models.QuerySet[Any]:
        try:
            titular = ContaService.obter_titular_autorizado(
                solicitante, titular_cpf=titular_cpf
            )
        except PermissaoNegadaTitular as exc:
            raise OcorrenciaNaoEncontrada(str(exc)) from exc

        qs = OcorrenciaPanico.objects.select_related("titular_pcd").filter(
            titular_pcd=titular
        )
        if data_inicio:
            qs = qs.filter(criado_em__date__gte=data_inicio)
        if data_fim:
            qs = qs.filter(criado_em__date__lte=data_fim)
        if status:
            qs = qs.filter(status=status)
        return qs.order_by("-criado_em", "-id")

