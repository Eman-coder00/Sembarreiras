from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from contas.exceptions import PermissaoNegadaTitular
from contas.services import ContaService
from equipamentos.exceptions import (
    AnexoInvalido,
    OperacaoEmprestimoInvalida,
    SolicitacaoEquipamentoNaoEncontrada,
)
from equipamentos.forms import (
    GerenciarPrazoEmprestimoForm,
    SolicitarEquipamentoForm,
)
from equipamentos.services import EquipamentoService


class EquipamentoListView(LoginRequiredMixin, View):
    def get(self, request):
        titular_cpf = request.GET.get("titular_cpf", "").strip() or None
        sem_vinculo_aprovado = False
        solicitacoes: Any = []
        alertas: Any = []
        try:
            beneficiario = ContaService.obter_titular_autorizado(
                request.user, titular_cpf=titular_cpf
            )
            solicitacoes = EquipamentoService.listar_solicitacoes_autorizadas(
                request.user, titular_cpf=titular_cpf
            )
            alertas = EquipamentoService.listar_alertas_vencimento(
                beneficiario
            )
        except (
            PermissaoNegadaTitular,
            SolicitacaoEquipamentoNaoEncontrada,
        ) as exc:
            solicitacoes = []
            alertas = []
            sem_vinculo_aprovado = True
            messages.warning(request, str(exc))

        return render(
            request,
            "equipamentos/lista.html",
            {
                "solicitacoes": solicitacoes,
                "alertas": alertas,
                "sem_vinculo_aprovado": sem_vinculo_aprovado,
            },
        )


class EquipamentoCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "equipamentos/solicitar.html",
            {"form": SolicitarEquipamentoForm()},
        )

    def post(self, request):
        form = SolicitarEquipamentoForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(
                request,
                "equipamentos/solicitar.html",
                {"form": form},
            )

        dados = form.cleaned_data
        try:
            solicitacao = EquipamentoService.criar_solicitacao(
                solicitante=request.user,
                tipo_equipamento=dados["tipo_equipamento"],
                largura_quadril_cm=dados["largura_quadril_cm"],
                altura_cm=dados["altura_cm"],
                peso_kg=dados["peso_kg"],
                arquivo_laudo=dados["arquivo_laudo"],
                arquivo_comprovante_residencia=dados[
                    "arquivo_comprovante_residencia"
                ],
                observacoes_clinicas=dados.get("observacoes_clinicas", ""),
                crm_medico=dados.get("crm_medico", ""),
                data_emissao_laudo=dados.get("data_emissao_laudo"),
                titular_cpf=dados.get("titular_cpf") or None,
            )
        except (SolicitacaoEquipamentoNaoEncontrada, AnexoInvalido) as exc:
            form.add_error(None, str(exc))
            messages.error(request, str(exc))
            return render(
                request,
                "equipamentos/solicitar.html",
                {"form": form},
            )

        messages.success(
            request,
            f"Solicitação enviada com sucesso! Protocolo: {solicitacao.protocolo}",
        )
        return redirect(
            "equipamentos:detalhe",
            protocolo=solicitacao.protocolo,
        )


class EquipamentoDetailView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str):
        try:
            solicitacao, eventos = (
                EquipamentoService.obter_detalhe_e_linha_tempo(
                    request.user, protocolo
                )
            )
        except SolicitacaoEquipamentoNaoEncontrada as exc:
            raise Http404 from exc

        return render(
            request,
            "equipamentos/detalhe.html",
            {
                "solicitacao": solicitacao,
                "eventos": eventos,
                "form_prazo": GerenciarPrazoEmprestimoForm(),
            },
        )


class EquipamentoAnexoDownloadView(LoginRequiredMixin, View):
    def get(self, request, protocolo: str, tipo_documento: str):
        try:
            campo_arquivo, content_type, nome_download = (
                EquipamentoService.obter_anexo_protegido(
                    request.user,
                    protocolo=protocolo,
                    tipo_documento=tipo_documento,
                )
            )
        except SolicitacaoEquipamentoNaoEncontrada as exc:
            raise Http404 from exc

        try:
            with campo_arquivo.open("rb") as arquivo_aberto:
                conteudo = arquivo_aberto.read()
        except OSError as exc:
            raise Http404 from exc

        return HttpResponse(
            conteudo,
            content_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{nome_download}"'
            },
        )


class EquipamentoPrazoView(LoginRequiredMixin, View):
    def post(self, request, protocolo: str):
        form = GerenciarPrazoEmprestimoForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Selecione uma opção válida de prazo.")
            return redirect("equipamentos:detalhe", protocolo=protocolo)

        dados = form.cleaned_data
        try:
            EquipamentoService.registrar_renovacao_ou_devolucao(
                solicitante=request.user,
                protocolo=protocolo,
                acao=dados["acao"],
                justificativa=dados.get("justificativa", ""),
            )
        except SolicitacaoEquipamentoNaoEncontrada as exc:
            raise Http404 from exc
        except OperacaoEmprestimoInvalida as exc:
            messages.error(request, str(exc))
            return redirect("equipamentos:detalhe", protocolo=protocolo)

        messages.success(
            request,
            "Solicitação de prazo/devolução registrada com sucesso.",
        )
        return redirect("equipamentos:detalhe", protocolo=protocolo)

