import hashlib
import hmac
import secrets
from datetime import date, datetime, time, timedelta
from typing import Any

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from agendamentos.exceptions import (
    AgendamentoNaoEncontrado,
    ComprovanteInvalido,
    PrazoMinimo24hConsulta,
    PrazoMinimo48hTransporte,
    SemVagaFrotaAdaptada,
    VagaIndisponivel,
)
from agendamentos.models import (
    Consulta,
    SolicitacaoTransporte,
    StatusConsulta,
    StatusTransporteHospitalar,
    VagaAgendaADEFAL,
    VagaFrotaAdaptada,
)
from contas.exceptions import PermissaoNegadaTitular
from contas.services import ContaService


def _combinar_data_hora_aware(data_ref: date, hora_ref: time) -> datetime:
    dt_ingenuo = datetime.combine(data_ref, hora_ref)
    if timezone.is_aware(timezone.now()):
        return timezone.make_aware(
            dt_ingenuo, timezone.get_current_timezone()
        )
    return dt_ingenuo


def _gerar_protocolo_consulta() -> str:
    hoje = timezone.localdate().strftime("%Y%m%d")
    for _ in range(10):
        sufixo = f"{secrets.randbelow(9000) + 1000}"
        protocolo = f"CNS-{hoje}-{sufixo}"
        if not Consulta.objects.filter(protocolo=protocolo).exists():
            return protocolo
    return f"CNS-{hoje}-{secrets.token_hex(2).upper()}"


class ComprovanteService:
    @staticmethod
    def gerar_assinatura(
        protocolo: str,
        cpf: str,
        data_iso: str,
        horario_iso: str,
    ) -> str:
        payload = f"{protocolo}|{cpf}|{data_iso}|{horario_iso}".encode("utf-8")
        chave = settings.SECRET_KEY.encode("utf-8")
        return hmac.new(chave, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def validar_comprovante(
        protocolo: str,
        assinatura: str,
    ) -> Consulta | Any:
        try:
            consulta = (
                Consulta.objects.select_related("paciente_pcd", "vaga")
                .get(protocolo=(protocolo or "").strip())
            )
        except Consulta.DoesNotExist as exc:
            raise ComprovanteInvalido(
                "Comprovante inválido: protocolo de consulta não localizado."
            ) from exc

        if consulta.status != StatusConsulta.CONFIRMADO:
            raise ComprovanteInvalido(
                "Comprovante inválido: a consulta não está ativa/confirmada."
            )

        assinatura_esperada = ComprovanteService.gerar_assinatura(
            protocolo=consulta.protocolo,
            cpf=consulta.paciente_pcd.cpf,
            data_iso=consulta.vaga.data.isoformat(),
            horario_iso=consulta.vaga.horario.isoformat(),
        )
        assinatura_informada = (assinatura or "").strip()

        if not assinatura_informada or not hmac.compare_digest(
            assinatura_esperada, assinatura_informada
        ):
            raise ComprovanteInvalido(
                "Assinatura digital HMAC do QR Code inválida ou adulterada."
            )

        return consulta


class AgendamentoService:
    @staticmethod
    def listar_vagas_disponiveis(
        *,
        especialidade: str | None = None,
        unidade: str | None = None,
        data: date | None = None,
    ) -> models.QuerySet[Any]:
        hoje = timezone.localdate()
        qs = VagaAgendaADEFAL.objects.filter(
            disponivel=True,
            data__gte=hoje,
        )
        if especialidade:
            qs = qs.filter(especialidade=especialidade)
        if unidade:
            qs = qs.filter(unidade=unidade)
        if data:
            qs = qs.filter(data=data)
        return qs.order_by("data", "horario")

    @staticmethod
    def listar_consultas_autorizadas(
        solicitante: Any,
        *,
        titular_cpf: str | None = None,
        status: int | None = None,
    ) -> models.QuerySet[Any]:
        try:
            paciente = ContaService.obter_titular_autorizado(
                solicitante, titular_cpf=titular_cpf
            )
        except PermissaoNegadaTitular as exc:
            raise AgendamentoNaoEncontrado(str(exc)) from exc

        qs = (
            Consulta.objects.select_related(
                "paciente_pcd",
                "solicitado_por",
                "vaga",
            )
            .prefetch_related("transporte", "transporte__frota")
            .filter(paciente_pcd=paciente)
        )
        if status:
            qs = qs.filter(status=int(status))
        return qs.order_by("-vaga__data", "-vaga__horario", "-id")

    @staticmethod
    def obter_consulta_autorizada(
        solicitante: Any,
        protocolo: str,
        *,
        permitir_staff: bool = False,
    ) -> Consulta | Any:
        try:
            consulta = (
                Consulta.objects.select_related(
                    "paciente_pcd",
                    "paciente_pcd__perfil_pcd",
                    "solicitado_por",
                    "vaga",
                )
                .get(protocolo=(protocolo or "").strip())
            )
        except Consulta.DoesNotExist as exc:
            raise AgendamentoNaoEncontrado(
                "Agendamento não encontrado."
            ) from exc

        if permitir_staff and getattr(solicitante, "is_staff", False):
            return consulta

        try:
            titular = ContaService.obter_titular_autorizado(
                solicitante,
                titular_cpf=consulta.paciente_pcd.cpf,
            )
        except PermissaoNegadaTitular as exc:
            raise AgendamentoNaoEncontrado(str(exc)) from exc

        if titular.pk != consulta.paciente_pcd_id:
            raise AgendamentoNaoEncontrado(
                "Usuário sem permissão para acessar este agendamento."
            )
        return consulta

    @staticmethod
    def agendar(
        solicitante: Any,
        vaga_id: int,
        *,
        titular_cpf: str | None = None,
    ) -> Consulta | Any:
        try:
            paciente = ContaService.obter_titular_autorizado(
                solicitante, titular_cpf=titular_cpf
            )
        except PermissaoNegadaTitular as exc:
            raise AgendamentoNaoEncontrado(str(exc)) from exc

        with transaction.atomic():
            try:
                vaga = VagaAgendaADEFAL.objects.select_for_update().get(
                    pk=vaga_id
                )
            except VagaAgendaADEFAL.DoesNotExist as exc:
                raise VagaIndisponivel(
                    "Horário selecionado não existe na agenda."
                ) from exc

            if not vaga.disponivel:
                raise VagaIndisponivel(
                    "Esta vaga já foi preenchida. Selecione outro horário disponível."
                )

            conflito = Consulta.objects.filter(
                paciente_pcd=paciente,
                status=StatusConsulta.CONFIRMADO,
                vaga__data=vaga.data,
                vaga__horario=vaga.horario,
            ).exists()
            if conflito:
                raise VagaIndisponivel(
                    "O paciente já possui outra consulta confirmada neste mesmo dia e horário."
                )

            vaga.disponivel = False
            vaga.save(update_fields=["disponivel"])

            protocolo = _gerar_protocolo_consulta()
            assinatura = ComprovanteService.gerar_assinatura(
                protocolo=protocolo,
                cpf=paciente.cpf,
                data_iso=vaga.data.isoformat(),
                horario_iso=vaga.horario.isoformat(),
            )

            return Consulta.objects.create(
                protocolo=protocolo,
                paciente_pcd=paciente,
                solicitado_por=solicitante,
                vaga=vaga,
                status=StatusConsulta.CONFIRMADO,
                assinatura_qr=assinatura,
            )

    @staticmethod
    def _verificar_antecedencia_24h(vaga: Any) -> None:
        instante_consulta = _combinar_data_hora_aware(vaga.data, vaga.horario)
        diferenca = instante_consulta - timezone.now()
        if diferenca < timedelta(hours=24):
            raise PrazoMinimo24hConsulta(
                "Cancelamentos e remarcações exigem antecedência mínima de 24 horas antes do atendimento."
            )

    @staticmethod
    def _liberar_transporte_se_existir(consulta: Any) -> None:
        transporte = (
            SolicitacaoTransporte.objects.select_related("frota")
            .filter(consulta=consulta)
            .first()
        )
        if (
            transporte
            and transporte.status != StatusTransporteHospitalar.CANCELADO
        ):
            frota = VagaFrotaAdaptada.objects.select_for_update().get(
                pk=transporte.frota_id
            )
            if frota.vagas_cadeirante_ocupadas > 0:
                frota.vagas_cadeirante_ocupadas -= 1
                frota.save(update_fields=["vagas_cadeirante_ocupadas"])
            transporte.status = StatusTransporteHospitalar.CANCELADO
            transporte.save(update_fields=["status"])

    @staticmethod
    def cancelar(
        solicitante: Any,
        protocolo: str,
        justificativa: str = "",
    ) -> Consulta | Any:
        consulta = AgendamentoService.obter_consulta_autorizada(
            solicitante, protocolo
        )
        if consulta.status != StatusConsulta.CONFIRMADO:
            raise VagaIndisponivel(
                "Apenas consultas confirmadas podem ser canceladas."
            )

        AgendamentoService._verificar_antecedencia_24h(consulta.vaga)

        with transaction.atomic():
            vaga = VagaAgendaADEFAL.objects.select_for_update().get(
                pk=consulta.vaga_id
            )
            vaga.disponivel = True
            vaga.save(update_fields=["disponivel"])

            AgendamentoService._liberar_transporte_se_existir(consulta)

            consulta.status = StatusConsulta.CANCELADO
            consulta.justificativa_alteracao = (
                justificativa or "Cancelado pelo usuário com antecedência regulamentar."
            )[:200]
            consulta.save(
                update_fields=["status", "justificativa_alteracao", "atualizado_em"]
            )
        return consulta

    @staticmethod
    def remarcar(
        solicitante: Any,
        protocolo: str,
        nova_vaga_id: int,
        justificativa: str = "",
    ) -> Consulta | Any:
        consulta_antiga = AgendamentoService.obter_consulta_autorizada(
            solicitante, protocolo
        )
        if consulta_antiga.status != StatusConsulta.CONFIRMADO:
            raise VagaIndisponivel(
                "Apenas consultas confirmadas podem ser remarcadas."
            )

        AgendamentoService._verificar_antecedencia_24h(consulta_antiga.vaga)

        with transaction.atomic():
            vaga_antiga = VagaAgendaADEFAL.objects.select_for_update().get(
                pk=consulta_antiga.vaga_id
            )
            try:
                nova_vaga = VagaAgendaADEFAL.objects.select_for_update().get(
                    pk=nova_vaga_id
                )
            except VagaAgendaADEFAL.DoesNotExist as exc:
                raise VagaIndisponivel(
                    "O novo horário selecionado não existe."
                ) from exc

            if not nova_vaga.disponivel:
                raise VagaIndisponivel(
                    "O novo horário selecionado já foi ocupado."
                )

            vaga_antiga.disponivel = True
            vaga_antiga.save(update_fields=["disponivel"])

            AgendamentoService._liberar_transporte_se_existir(consulta_antiga)

            consulta_antiga.status = StatusConsulta.REAGENDADO
            consulta_antiga.justificativa_alteracao = (
                justificativa or "Remarcado pelo usuário."
            )[:200]
            consulta_antiga.save(
                update_fields=["status", "justificativa_alteracao", "atualizado_em"]
            )

            nova_vaga.disponivel = False
            nova_vaga.save(update_fields=["disponivel"])

            novo_protocolo = _gerar_protocolo_consulta()
            nova_assinatura = ComprovanteService.gerar_assinatura(
                protocolo=novo_protocolo,
                cpf=consulta_antiga.paciente_pcd.cpf,
                data_iso=nova_vaga.data.isoformat(),
                horario_iso=nova_vaga.horario.isoformat(),
            )

            return Consulta.objects.create(
                protocolo=novo_protocolo,
                paciente_pcd=consulta_antiga.paciente_pcd,
                solicitado_por=solicitante,
                vaga=nova_vaga,
                status=StatusConsulta.CONFIRMADO,
                assinatura_qr=nova_assinatura,
            )


class TransporteHospitalarService:
    @staticmethod
    def obter_endereco_padrao_embarque(consulta: Any) -> str:
        perfil = getattr(consulta.paciente_pcd, "perfil_pcd", None)
        if not perfil:
            return "Maceió - AL"
        complemento = f" ({perfil.complemento})" if perfil.complemento else ""
        return (
            f"{perfil.logradouro}, {perfil.numero}{complemento} - "
            f"{perfil.bairro}, {perfil.municipio}/{perfil.uf} (CEP {perfil.cep})"
        )

    @staticmethod
    def solicitar_transporte(
        solicitante: Any,
        *,
        protocolo_consulta: str,
        endereco_embarque: str,
        precisa_acompanhante: bool,
        equipamento_transporte: str,
    ) -> SolicitacaoTransporte | Any:
        consulta = AgendamentoService.obter_consulta_autorizada(
            solicitante, protocolo_consulta
        )
        if consulta.status != StatusConsulta.CONFIRMADO:
            raise VagaIndisponivel(
                "O transporte adaptado só pode ser solicitado para consultas confirmadas."
            )

        instante_consulta = _combinar_data_hora_aware(
            consulta.vaga.data, consulta.vaga.horario
        )
        if (instante_consulta - timezone.now()) < timedelta(hours=48):
            raise PrazoMinimo48hTransporte(
                "A solicitação de transporte hospitalar adaptado exige antecedência mínima de 48 horas antes da consulta."
            )

        with transaction.atomic():
            existente = (
                SolicitacaoTransporte.objects.select_for_update()
                .filter(consulta=consulta)
                .first()
            )
            if (
                existente
                and existente.status != StatusTransporteHospitalar.CANCELADO
            ):
                raise VagaIndisponivel(
                    "Já existe um transporte adaptado confirmado para esta consulta."
                )

            frotas_candidatas = (
                VagaFrotaAdaptada.objects.select_for_update()
                .filter(data=consulta.vaga.data)
                .order_by("turno_horario", "id")
            )
            frota_selecionada = None
            for frota in frotas_candidatas:
                if (
                    frota.vagas_cadeirante_ocupadas
                    < frota.vagas_cadeirante_total
                ):
                    frota_selecionada = frota
                    break

            if not frota_selecionada:
                raise SemVagaFrotaAdaptada(
                    "Sem vagas disponíveis na frota adaptada da ADEFAL para a data desta consulta."
                )

            frota_selecionada.vagas_cadeirante_ocupadas += 1
            frota_selecionada.save(update_fields=["vagas_cadeirante_ocupadas"])

            dt_apanhe = datetime.combine(
                consulta.vaga.data, consulta.vaga.horario
            ) - timedelta(hours=1)
            horario_apanhe = dt_apanhe.time()

            if existente:
                existente.frota = frota_selecionada
                existente.endereco_embarque = endereco_embarque.strip()
                existente.precisa_acompanhante = bool(precisa_acompanhante)
                existente.equipamento_transporte = equipamento_transporte
                existente.horario_apanhe_previsto = horario_apanhe
                existente.status = StatusTransporteHospitalar.ROTA_CONFIRMADA
                existente.save()
                return existente

            return SolicitacaoTransporte.objects.create(
                consulta=consulta,
                frota=frota_selecionada,
                endereco_embarque=endereco_embarque.strip(),
                precisa_acompanhante=bool(precisa_acompanhante),
                equipamento_transporte=equipamento_transporte,
                horario_apanhe_previsto=horario_apanhe,
                status=StatusTransporteHospitalar.ROTA_CONFIRMADA,
            )

    @staticmethod
    def cancelar_transporte(
        solicitante: Any,
        protocolo_consulta: str,
    ) -> SolicitacaoTransporte | Any:
        consulta = AgendamentoService.obter_consulta_autorizada(
            solicitante, protocolo_consulta
        )
        AgendamentoService._verificar_antecedencia_24h(consulta.vaga)

        with transaction.atomic():
            transporte = (
                SolicitacaoTransporte.objects.select_for_update()
                .filter(consulta=consulta)
                .first()
            )
            if (
                not transporte
                or transporte.status == StatusTransporteHospitalar.CANCELADO
            ):
                raise AgendamentoNaoEncontrado(
                    "Nenhuma reserva ativa de transporte encontrada para esta consulta."
                )

            frota = VagaFrotaAdaptada.objects.select_for_update().get(
                pk=transporte.frota_id
            )
            if frota.vagas_cadeirante_ocupadas > 0:
                frota.vagas_cadeirante_ocupadas -= 1
                frota.save(update_fields=["vagas_cadeirante_ocupadas"])

            transporte.status = StatusTransporteHospitalar.CANCELADO
            transporte.save(update_fields=["status"])
            return transporte

