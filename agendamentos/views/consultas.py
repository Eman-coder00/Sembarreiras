from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from agendamentos.exceptions import (
    AgendamentoNaoEncontrado,
    ComprovanteInvalido,
    PrazoMinimo24hConsulta,
    PrazoMinimo48hTransporte,
    SemVagaFrotaAdaptada,
    VagaIndisponivel,
)
from agendamentos.forms import (
    AgendarConsultaForm,
    CancelarConsultaForm,
    FiltroMeusAgendamentosForm,
    FiltroVagasADEFALForm,
    RemarcarConsultaForm,
    SolicitarTransporteHospitalarForm,
    ValidarComprovanteQRForm,
)
from agendamentos.services import (
    AgendamentoService,
    ComprovanteService,
    TransporteHospitalarService,
)


class ConsultaListView(LoginRequiredMixin, View):
    def get(self, request):
        form = FiltroMeusAgendamentosForm(request.GET or None)
        titular_cpf = None
        status = None
        if form.is_valid():
            titular_cpf = form.cleaned_data.get("titular_cpf") or None
            status_val = form.cleaned_data.get("status")
            status = int(status_val) if status_val else None

        sem_vinculo_aprovado = False
        consultas: Any = []
        try:
            consultas = AgendamentoService.listar_consultas_autorizadas(
                request.user,
                titular_cpf=titular_cpf,
                status=status,
            )
        except AgendamentoNaoEncontrado as exc:
            consultas = []
            sem_vinculo_aprovado = True
            messages.warning(request, str(exc))

        return render(
            request,
            "agendamentos/lista.html",
            {
                "consultas": consultas,
                "form": form,
                "sem_vinculo_aprovado": sem_vinculo_aprovado,
            },
        )


class ConsultaCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form_filtro = FiltroVagasADEFALForm(request.GET or None)
        especialidade = None
        unidade = None
        data = None
        if form_filtro.is_valid():
            especialidade = form_filtro.cleaned_data.get("especialidade") or None
            unidade = form_filtro.cleaned_data.get("unidade") or None
            data = form_filtro.cleaned_data.get("data")

        vagas = AgendamentoService.listar_vagas_disponiveis(
            especialidade=especialidade,
            unidade=unidade,
            data=data,
        )
        return render(
            request,
            "agendamentos/criar.html",
            {
                "form_filtro": form_filtro,
                "form_agendar": AgendarConsultaForm(),
                "vagas": vagas,
            },
        )

    def post(self, request):
        form = AgendarConsultaForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Selecione um horário disponível válido.")
            return redirect("agendamentos:criar")

        dados = form.cleaned_data
        try:
            consulta = AgendamentoService.agendar(
                solicitante=request.user,
                vaga_id=dados["vaga_id"],
                titular_cpf=dados.get("titular_cpf") or None,
            )
        except AgendamentoNaoEncontrado as exc:
            # Cuidador sem vínculo aprovado é orientado na própria tela de criação
            messages.error(
                request,
                f"{exc} Confirme o código OTP com o titular PCD na tela de Vínculos ou verifique o CPF informado.",
            )
            return redirect("agendamentos:criar")
        except VagaIndisponivel as exc:
            messages.error(request, str(exc))
            return redirect("agendamentos:criar")

        messages.success(
            request,
            f"Agendamento confirmado! Protocolo: {consulta.protocolo}",
        )
        return redirect("agendamentos:detalhe", protocolo=consulta.protocolo)


class ConsultaDetailView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str):
        try:
            consulta = AgendamentoService.obter_consulta_autorizada(
                request.user, protocolo
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc

        transporte = getattr(consulta, "transporte", None)
        return render(
            request,
            "agendamentos/detalhe.html",
            {
                "consulta": consulta,
                "transporte": transporte,
                "form_cancelar": CancelarConsultaForm(),
            },
        )


class ConsultaCancelarView(LoginRequiredMixin, View):
    def post(self, request, protocolo: str):
        form = CancelarConsultaForm(request.POST)
        justificativa = ""
        if form.is_valid():
            justificativa = form.cleaned_data.get("justificativa", "")

        try:
            AgendamentoService.cancelar(
                solicitante=request.user,
                protocolo=protocolo,
                justificativa=justificativa,
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc
        except (PrazoMinimo24hConsulta, VagaIndisponivel) as exc:
            messages.error(request, str(exc))
            return redirect("agendamentos:detalhe", protocolo=protocolo)

        messages.success(
            request,
            "Agendamento cancelado com sucesso e vaga liberada.",
        )
        return redirect("agendamentos:lista")


class ConsultaRemarcarView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str):
        try:
            consulta = AgendamentoService.obter_consulta_autorizada(
                request.user, protocolo
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc

        vagas = AgendamentoService.listar_vagas_disponiveis(
            especialidade=consulta.vaga.especialidade
        )
        return render(
            request,
            "agendamentos/remarcar.html",
            {
                "consulta": consulta,
                "vagas": vagas,
                "form": RemarcarConsultaForm(),
            },
        )

    def post(self, request, protocolo: str):
        form = RemarcarConsultaForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Selecione um novo horário válido.")
            return redirect("agendamentos:remarcar", protocolo=protocolo)

        dados = form.cleaned_data
        try:
            nova_consulta = AgendamentoService.remarcar(
                solicitante=request.user,
                protocolo=protocolo,
                nova_vaga_id=dados["nova_vaga_id"],
                justificativa=dados.get("justificativa", ""),
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc
        except (PrazoMinimo24hConsulta, VagaIndisponivel) as exc:
            messages.error(request, str(exc))
            return redirect("agendamentos:remarcar", protocolo=protocolo)

        messages.success(
            request,
            f"Consulta remarcada com sucesso! Novo protocolo: {nova_consulta.protocolo}",
        )
        return redirect(
            "agendamentos:detalhe",
            protocolo=nova_consulta.protocolo,
        )


class TransporteSolicitarView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str):
        try:
            consulta = AgendamentoService.obter_consulta_autorizada(
                request.user, protocolo
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc

        endereco_padrao = (
            TransporteHospitalarService.obter_endereco_padrao_embarque(consulta)
        )
        form = SolicitarTransporteHospitalarForm(
            initial={"endereco_embarque": endereco_padrao}
        )
        return render(
            request,
            "agendamentos/solicitar_transporte.html",
            {"consulta": consulta, "form": form},
        )

    def post(self, request, protocolo: str):
        try:
            consulta = AgendamentoService.obter_consulta_autorizada(
                request.user, protocolo
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc

        form = SolicitarTransporteHospitalarForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "agendamentos/solicitar_transporte.html",
                {"consulta": consulta, "form": form},
            )

        dados = form.cleaned_data
        try:
            TransporteHospitalarService.solicitar_transporte(
                solicitante=request.user,
                protocolo_consulta=protocolo,
                endereco_embarque=dados["endereco_embarque"],
                precisa_acompanhante=dados["precisa_acompanhante"],
                equipamento_transporte=dados["equipamento_transporte"],
            )
        except (
            PrazoMinimo48hTransporte,
            SemVagaFrotaAdaptada,
            VagaIndisponivel,
        ) as exc:
            form.add_error(None, str(exc))
            messages.error(request, str(exc))
            return render(
                request,
                "agendamentos/solicitar_transporte.html",
                {"consulta": consulta, "form": form},
            )

        messages.success(
            request,
            "Transporte hospitalar adaptado reservado com sucesso!",
        )
        return redirect("agendamentos:detalhe", protocolo=protocolo)


class TransporteCancelarView(LoginRequiredMixin, View):
    def post(self, request, protocolo: str):
        try:
            TransporteHospitalarService.cancelar_transporte(
                solicitante=request.user,
                protocolo_consulta=protocolo,
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc
        except PrazoMinimo24hConsulta as exc:
            messages.error(request, str(exc))
            return redirect("agendamentos:detalhe", protocolo=protocolo)

        messages.success(
            request,
            "Reserva de transporte adaptada cancelada e vaga devolvida à frota.",
        )
        return redirect("agendamentos:detalhe", protocolo=protocolo)


class ComprovanteDigitalView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str):
        try:
            consulta = AgendamentoService.obter_consulta_autorizada(
                request.user,
                protocolo,
                permitir_staff=True,
            )
        except AgendamentoNaoEncontrado as exc:
            raise Http404 from exc

        transporte = getattr(consulta, "transporte", None)
        return render(
            request,
            "agendamentos/comprovante.html",
            {
                "consulta": consulta,
                "transporte": transporte,
            },
        )


class PortariaValidarQRView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_staff:
            raise Http404
        return render(
            request,
            "agendamentos/validar_qr.html",
            {"form": ValidarComprovanteQRForm()},
        )

    def post(self, request):
        if not request.user.is_staff:
            raise Http404
        form = ValidarComprovanteQRForm(request.POST)
        consulta_validada = None
        if form.is_valid():
            dados = form.cleaned_data
            try:
                consulta_validada = ComprovanteService.validar_comprovante(
                    protocolo=dados["protocolo"],
                    assinatura=dados["assinatura"],
                )
                messages.success(
                    request,
                    f"Comprovante autêntico! Acesso liberado para {consulta_validada.paciente_pcd.nome_completo}.",
                )
            except ComprovanteInvalido as exc:
                form.add_error(None, str(exc))
                messages.error(request, str(exc))

        return render(
            request,
            "agendamentos/validar_qr.html",
            {
                "form": form,
                "consulta_validada": consulta_validada,
            },
        )

