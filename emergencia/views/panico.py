from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View

from emergencia.exceptions import (
    JanelaCancelamentoEncerrada,
    LimiteContatosExcedido,
    MinimoContatoAtivoObrigatorio,
    OcorrenciaNaoEncontrada,
    SemContatosDeEmergencia,
)
from emergencia.forms import (
    AcionarPanicoForm,
    ContatoEmergenciaForm,
    DispararPanicoForm,
    FiltroHistoricoPanicoForm,
)
from emergencia.services import ContatoEmergenciaService, PanicoService


class ContatoEmergenciaListView(LoginRequiredMixin, View):
    def get(self, request):
        contatos = ContatoEmergenciaService.listar_ativos(request.user)
        return render(
            request,
            "emergencia/contatos.html",
            {
                "contatos": contatos,
                "form": ContatoEmergenciaForm(),
            },
        )

    def post(self, request):
        form = ContatoEmergenciaForm(request.POST)
        contatos = ContatoEmergenciaService.listar_ativos(request.user)
        if not form.is_valid():
            return render(
                request,
                "emergencia/contatos.html",
                {"contatos": contatos, "form": form},
            )

        dados = form.cleaned_data
        try:
            ContatoEmergenciaService.criar(
                titular_pcd=request.user,
                nome=dados["nome"],
                telefone=dados["telefone"],
                parentesco=dados["parentesco"],
                prioridade=dados["prioridade"],
            )
        except LimiteContatosExcedido as exc:
            form.add_error(None, str(exc))
            messages.error(request, str(exc))
            return render(
                request,
                "emergencia/contatos.html",
                {"contatos": contatos, "form": form},
            )

        messages.success(
            request,
            "Contato de emergência prioritário cadastrado com sucesso.",
        )
        return redirect("emergencia:contatos")


class ContatoEmergenciaUpdateView(LoginRequiredMixin, View):
    def get(self, request, contato_id: int):
        try:
            contato = ContatoEmergenciaService.obter_do_titular(
                contato_id, request.user
            )
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc

        form = ContatoEmergenciaForm(
            initial={
                "nome": contato.nome,
                "telefone": contato.telefone,
                "parentesco": contato.parentesco,
                "prioridade": contato.prioridade,
                "status": contato.status,
            }
        )
        return render(
            request,
            "emergencia/editar_contato.html",
            {"contato": contato, "form": form},
        )

    def post(self, request, contato_id: int):
        try:
            contato = ContatoEmergenciaService.obter_do_titular(
                contato_id, request.user
            )
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc

        form = ContatoEmergenciaForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "emergencia/editar_contato.html",
                {"contato": contato, "form": form},
            )

        dados = form.cleaned_data
        try:
            ContatoEmergenciaService.atualizar(
                contato_id=contato.id,
                titular_pcd=request.user,
                nome=dados["nome"],
                telefone=dados["telefone"],
                parentesco=dados["parentesco"],
                prioridade=dados["prioridade"],
                status=dados["status"],
            )
        except (LimiteContatosExcedido, MinimoContatoAtivoObrigatorio) as exc:
            form.add_error(None, str(exc))
            messages.error(request, str(exc))
            return render(
                request,
                "emergencia/editar_contato.html",
                {"contato": contato, "form": form},
            )

        messages.success(request, "Contato de emergência atualizado com sucesso.")
        return redirect("emergencia:contatos")


class ContatoEmergenciaDeleteView(LoginRequiredMixin, View):
    def post(self, request, contato_id: int):
        try:
            ContatoEmergenciaService.excluir(contato_id, request.user)
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc
        except MinimoContatoAtivoObrigatorio as exc:
            messages.error(request, str(exc))
            return redirect("emergencia:contatos")

        messages.success(request, "Contato de emergência removido.")
        return redirect("emergencia:contatos")


class BotaoPanicoView(LoginRequiredMixin, View):
    def get(self, request):
        contatos = ContatoEmergenciaService.listar_ativos(request.user)
        contatos_json = ContatoEmergenciaService.listar_json_sincronizacao(
            request.user
        )
        return render(
            request,
            "emergencia/panico.html",
            {
                "contatos": contatos,
                "contatos_json": contatos_json,
                "form": AcionarPanicoForm(),
            },
        )

    def post(self, request):
        form = AcionarPanicoForm(request.POST)
        latitude = None
        longitude = None
        if form.is_valid():
            latitude = form.cleaned_data.get("latitude")
            longitude = form.cleaned_data.get("longitude")

        try:
            ocorrencia = PanicoService.iniciar_acionamento(
                titular_pcd=request.user,
                latitude=latitude,
                longitude=longitude,
            )
        except SemContatosDeEmergencia as exc:
            messages.error(request, str(exc))
            return redirect("emergencia:contatos")

        return redirect(
            "emergencia:contagem",
            ocorrencia_id=ocorrencia.id,
        )


class ContagemRegressivaView(LoginRequiredMixin, View):
    def get(self, request, ocorrencia_id: int):
        try:
            ocorrencia = PanicoService.obter_ocorrencia_do_titular(
                ocorrencia_id, request.user
            )
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc

        contatos = ContatoEmergenciaService.listar_ativos(request.user)
        return render(
            request,
            "emergencia/contagem.html",
            {
                "ocorrencia": ocorrencia,
                "contatos": contatos,
                "form_disparo": DispararPanicoForm(
                    initial={
                        "latitude": ocorrencia.latitude,
                        "longitude": ocorrencia.longitude,
                    }
                ),
            },
        )


class CancelarPanicoView(LoginRequiredMixin, View):
    def post(self, request, ocorrencia_id: int):
        try:
            PanicoService.cancelar_alerta(ocorrencia_id, request.user)
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc
        except JanelaCancelamentoEncerrada as exc:
            messages.error(request, str(exc))
            return redirect("emergencia:historico")

        messages.success(request, "Alerta cancelado com sucesso")
        return redirect("emergencia:panico")


class DispararPanicoView(LoginRequiredMixin, View):
    def post(self, request, ocorrencia_id: int):
        form = DispararPanicoForm(request.POST)
        latitude = None
        longitude = None
        falha_dados = False
        if form.is_valid():
            latitude = form.cleaned_data.get("latitude")
            longitude = form.cleaned_data.get("longitude")
            falha_dados = bool(form.cleaned_data.get("falha_dados"))

        try:
            ocorrencia = PanicoService.confirmar_disparo(
                ocorrencia_id=ocorrencia_id,
                titular_pcd=request.user,
                latitude=latitude,
                longitude=longitude,
                falha_dados=falha_dados,
            )
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc
        except (JanelaCancelamentoEncerrada, SemContatosDeEmergencia) as exc:
            messages.error(request, str(exc))
            return redirect("emergencia:panico")

        messages.warning(
            request,
            f"Alerta de emergência {ocorrencia.codigo} enviado aos contatos prioritários!",
        )
        return redirect("emergencia:historico")


class HistoricoPanicoView(LoginRequiredMixin, View):
    def get(self, request):
        form = FiltroHistoricoPanicoForm(request.GET or None)
        titular_cpf = None
        data_inicio = None
        data_fim = None
        status = None

        if form.is_valid():
            titular_cpf = form.cleaned_data.get("titular_cpf") or None
            data_inicio = form.cleaned_data.get("data_inicio")
            data_fim = form.cleaned_data.get("data_fim")
            status = form.cleaned_data.get("status") or None

        try:
            ocorrencias = PanicoService.listar_historico(
                request.user,
                titular_cpf=titular_cpf,
                data_inicio=data_inicio,
                data_fim=data_fim,
                status=status,
            )
        except OcorrenciaNaoEncontrada as exc:
            raise Http404 from exc

        return render(
            request,
            "emergencia/historico.html",
            {
                "ocorrencias": ocorrencias,
                "form": form,
            },
        )
