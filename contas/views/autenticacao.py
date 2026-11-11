from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View

from contas.exceptions import (
    CepNaoLocalizado,
    ContaTemporariamenteBloqueada,
    CpfJaCadastrado,
    CredenciaisInvalidas,
    EmailJaCadastrado,
    SenhaAtualInvalida,
    TokenRecuperacaoInvalido,
    VinculoInvalido,
)
from contas.forms import (
    AcessibilidadeMotoraForm,
    CadastroCuidadorForm,
    CadastroPCDForm,
    ConfirmarVinculoOTPForm,
    InativarContaForm,
    LoginPerfilForm,
    PerfilPCDEditarForm,
    RedefinirSenhaForm,
    SolicitarRecuperacaoSenhaForm,
)
from contas.models import PapelUsuario, TimeoutTela
from contas.services import (
    AutenticacaoService,
    ContaService,
    VinculoCuidadorService,
)


def _obter_ip(request: HttpRequest) -> str:
    return request.META.get("REMOTE_ADDR", "") or ""


class HomeView(LoginRequiredMixin, View):
    def get(self, request):
        resumo = ContaService.obter_resumo_home(request.user)
        return render(
            request,
            "contas/home.html",
            resumo,
        )


class NotificacoesView(LoginRequiredMixin, View):
    def get(self, request):
        notificacoes = ContaService.listar_notificacoes(request.user)
        return render(
            request,
            "contas/notificacoes.html",
            {"notificacoes": notificacoes},
        )


class PainelInicialView(LoginRequiredMixin, View):
    def get(self, request):
        perfil = ContaService.obter_perfil_pcd(request.user)
        vinculos = VinculoCuidadorService.listar_vinculos(request.user)
        logs = ContaService.listar_logs_recentes(request.user)
        return render(
            request,
            "contas/painel.html",
            {
                "perfil": perfil,
                "vinculos": vinculos,
                "logs": logs,
                "form_inativar": InativarContaForm(),
            },
        )


class EntrarView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("contas:home")
        return render(
            request,
            "contas/entrar.html",
            {
                "form": LoginPerfilForm(
                    initial={"perfil_selecionado": PapelUsuario.PCD}
                ),
                "next": request.GET.get("next", ""),
            },
        )

    def post(self, request):
        form = LoginPerfilForm(request.POST)
        next_url = request.POST.get("next", "")
        if not form.is_valid():
            return render(
                request,
                "contas/entrar.html",
                {"form": form, "next": next_url},
            )

        dados = form.cleaned_data
        try:
            usuario = AutenticacaoService.autenticar(
                identificador=dados["identificador"],
                senha=dados["senha"],
                perfil_selecionado=dados["perfil_selecionado"],
                ip=_obter_ip(request),
            )
        except ContaTemporariamenteBloqueada as exc:
            form.add_error(None, str(exc))
            return render(
                request,
                "contas/entrar.html",
                {"form": form, "next": next_url},
            )
        except CredenciaisInvalidas as exc:
            form.add_error(None, str(exc))
            return render(
                request,
                "contas/entrar.html",
                {"form": form, "next": next_url},
            )

        login(request, usuario)
        request.session["perfil_ativo"] = dados["perfil_selecionado"]

        if dados.get("manter_conectado"):
            request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            perfil = ContaService.obter_perfil_pcd(usuario)
            if perfil and perfil.timeout_tela == TimeoutTela.PROLONGADO_10M:
                request.session.set_expiry(60 * 10)
            else:
                request.session.set_expiry(0)

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect("contas:home")


class SairView(LoginRequiredMixin, View):
    def post(self, request):
        logout(request)
        return redirect("contas:entrar")


class CadastroPCDView(View):
    def get(self, request):
        cep_busca = request.GET.get("cep_busca", "").strip()
        initial: dict[str, str] = {}
        if cep_busca:
            initial["cep"] = cep_busca
            try:
                endereco = ContaService.consultar_cep(cep_busca)
                initial.update(endereco)
            except CepNaoLocalizado as exc:
                messages.warning(request, str(exc))
        return render(
            request,
            "contas/cadastro_pcd.html",
            {"form": CadastroPCDForm(initial=initial)},
        )

    def post(self, request):
        form = CadastroPCDForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Campo(s) obrigatório(s) não preenchido(s)")
            return render(request, "contas/cadastro_pcd.html", {"form": form})

        dados = form.cleaned_data
        try:
            usuario = ContaService.cadastrar_pcd(
                cpf=dados["cpf"],
                nome_completo=dados["nome_completo"],
                data_nascimento=dados["data_nascimento"],
                telefone=dados["telefone"],
                email=dados["email"],
                senha=dados["senha"],
                tipo_deficiencia=dados["tipo_deficiencia"],
                equipamentos_apoio=dados["equipamentos_apoio"],
                cep=dados["cep"],
                logradouro=dados["logradouro"],
                numero=dados["numero"],
                complemento=dados.get("complemento", ""),
                bairro=dados["bairro"],
                municipio=dados["municipio"],
                uf=dados["uf"],
                ip=_obter_ip(request),
            )
        except CpfJaCadastrado as exc:
            form.add_error("cpf", str(exc))
            return render(request, "contas/cadastro_pcd.html", {"form": form})
        except EmailJaCadastrado as exc:
            form.add_error("email", str(exc))
            return render(request, "contas/cadastro_pcd.html", {"form": form})

        login(request, usuario)
        messages.success(request, "Cadastro realizado com sucesso")
        return redirect("contas:home")


class ConsultarCepView(View):
    def get(self, request):
        cep = request.GET.get("cep", "")
        try:
            dados = ContaService.consultar_cep(cep)
        except CepNaoLocalizado as exc:
            return JsonResponse({"encontrado": False, "mensagem": str(exc)}, status=404)
        return JsonResponse({"encontrado": True, **dados})


class CadastroCuidadorView(View):
    def get(self, request):
        return render(
            request,
            "contas/cadastro_cuidador.html",
            {"form": CadastroCuidadorForm()},
        )

    def post(self, request):
        form = CadastroCuidadorForm(request.POST)
        if not form.is_valid():
            return render(request, "contas/cadastro_cuidador.html", {"form": form})

        dados = form.cleaned_data
        try:
            vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
                cpf_cuidador=dados["cpf_cuidador"],
                nome_completo=dados["nome_completo"],
                email=dados["email"],
                telefone=dados["telefone"],
                senha=dados["senha"],
                cpf_titular_pcd=dados["cpf_titular_pcd"],
                grau_parentesco=dados["grau_parentesco"],
                ip=_obter_ip(request),
            )
        except CpfJaCadastrado as exc:
            form.add_error("cpf_cuidador", str(exc))
            return render(request, "contas/cadastro_cuidador.html", {"form": form})
        except EmailJaCadastrado as exc:
            form.add_error("email", str(exc))
            return render(request, "contas/cadastro_cuidador.html", {"form": form})
        except VinculoInvalido as exc:
            form.add_error("cpf_titular_pcd", str(exc))
            return render(request, "contas/cadastro_cuidador.html", {"form": form})

        login(request, vinculo.cuidador)
        messages.info(
            request,
            "Solicitação de vínculo criada. Confirme o código OTP enviado ao titular PCD.",
        )
        return redirect("contas:vinculos")


class PerfilEditarView(LoginRequiredMixin, View):
    def get(self, request):
        perfil = ContaService.obter_perfil_pcd(request.user)
        if not perfil:
            raise Http404
        titular = perfil.usuario
        form = PerfilPCDEditarForm(
            initial={
                "nome_completo": titular.nome_completo,
                "telefone": titular.telefone,
                "equipamentos_apoio": [
                    item for item in perfil.equipamentos_apoio.split(",") if item
                ],
                "cep": perfil.cep,
                "logradouro": perfil.logradouro,
                "numero": perfil.numero,
                "complemento": perfil.complemento,
                "bairro": perfil.bairro,
                "municipio": perfil.municipio,
                "uf": perfil.uf,
            }
        )
        return render(
            request,
            "contas/perfil_editar.html",
            {"form": form, "perfil": perfil},
        )

    def post(self, request):
        perfil = ContaService.obter_perfil_pcd(request.user)
        if not perfil:
            raise Http404
        form = PerfilPCDEditarForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "contas/perfil_editar.html",
                {"form": form, "perfil": perfil},
            )

        dados = form.cleaned_data
        try:
            ContaService.atualizar_dados_pcd(
                request.user,
                nome_completo=dados["nome_completo"],
                telefone=dados["telefone"],
                equipamentos_apoio=dados["equipamentos_apoio"],
                cep=dados["cep"],
                logradouro=dados["logradouro"],
                numero=dados["numero"],
                complemento=dados.get("complemento", ""),
                bairro=dados["bairro"],
                municipio=dados["municipio"],
                uf=dados["uf"],
                senha_atual=dados.get("senha_atual", ""),
                ip=_obter_ip(request),
            )
        except SenhaAtualInvalida as exc:
            form.add_error("senha_atual", str(exc))
            return render(
                request,
                "contas/perfil_editar.html",
                {"form": form, "perfil": perfil},
            )

        messages.success(request, "Dados do perfil atualizados com sucesso.")
        return redirect("contas:painel")


class AcessibilidadeView(LoginRequiredMixin, View):
    def get(self, request):
        perfil = ContaService.obter_perfil_pcd(request.user)
        if not perfil:
            raise Http404
        form = AcessibilidadeMotoraForm(
            initial={
                "tipo_deficiencia": perfil.tipo_deficiencia,
                "equipamentos_apoio": [
                    item for item in perfil.equipamentos_apoio.split(",") if item
                ],
                "tamanho_toque": perfil.tamanho_toque,
                "timeout_tela": perfil.timeout_tela,
                "alto_contraste": perfil.alto_contraste,
            }
        )
        return render(
            request,
            "contas/acessibilidade.html",
            {"form": form, "perfil": perfil},
        )

    def post(self, request):
        perfil = ContaService.obter_perfil_pcd(request.user)
        if not perfil:
            raise Http404
        form = AcessibilidadeMotoraForm(request.POST)
        if not form.is_valid():
            return render(
                request,
                "contas/acessibilidade.html",
                {"form": form, "perfil": perfil},
            )

        dados = form.cleaned_data
        perfil = ContaService.atualizar_acessibilidade(
            request.user,
            tipo_deficiencia=dados["tipo_deficiencia"],
            equipamentos_apoio=dados["equipamentos_apoio"],
            tamanho_toque=dados["tamanho_toque"],
            timeout_tela=dados["timeout_tela"],
            alto_contraste=dados["alto_contraste"],
            ip=_obter_ip(request),
        )
        if perfil.timeout_tela == TimeoutTela.PROLONGADO_10M:
            request.session.set_expiry(60 * 10)
        messages.success(request, "Perfil de acessibilidade atualizado com sucesso")
        return redirect("contas:acessibilidade")


class ContaInativarView(LoginRequiredMixin, View):
    def post(self, request):
        form = InativarContaForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Informe sua senha atual para inativar a conta.")
            return redirect("contas:painel")

        try:
            ContaService.inativar_conta_lgpd(
                request.user,
                senha_atual=form.cleaned_data["senha_atual"],
                ip=_obter_ip(request),
            )
        except SenhaAtualInvalida as exc:
            messages.error(request, str(exc))
            return redirect("contas:painel")

        logout(request)
        messages.success(
            request,
            "Conta inativada e dados pessoais anonimizados conforme a LGPD.",
        )
        return redirect("contas:entrar")


class VinculoListView(LoginRequiredMixin, View):
    def get(self, request):
        vinculos = VinculoCuidadorService.listar_vinculos(request.user)
        return render(
            request,
            "contas/vinculos.html",
            {
                "vinculos": vinculos,
                "form_otp": ConfirmarVinculoOTPForm(),
            },
        )


class VinculoConfirmarView(LoginRequiredMixin, View):
    def post(self, request, vinculo_id: int):
        form = ConfirmarVinculoOTPForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Informe um código OTP válido de 6 dígitos.")
            return redirect("contas:vinculos")

        try:
            VinculoCuidadorService.confirmar_vinculo(
                vinculo_id=vinculo_id,
                codigo_otp=form.cleaned_data["codigo_otp"],
                solicitante=request.user,
                ip=_obter_ip(request),
            )
        except VinculoInvalido as exc:
            messages.error(request, str(exc))
            return redirect("contas:vinculos")

        messages.success(request, "Vínculo estabelecido com sucesso")
        return redirect("contas:vinculos")


class VinculoRevogarView(LoginRequiredMixin, View):
    def post(self, request, vinculo_id: int):
        try:
            VinculoCuidadorService.revogar_vinculo(
                vinculo_id=vinculo_id,
                solicitante=request.user,
                ip=_obter_ip(request),
            )
        except VinculoInvalido as exc:
            raise Http404 from exc

        messages.success(request, "Vínculo revogado com sucesso.")
        return redirect("contas:vinculos")


class SenhaRecuperarView(View):
    def get(self, request):
        return render(
            request,
            "contas/recuperar_senha.html",
            {"form": SolicitarRecuperacaoSenhaForm()},
        )

    def post(self, request):
        form = SolicitarRecuperacaoSenhaForm(request.POST)
        if not form.is_valid():
            return render(request, "contas/recuperar_senha.html", {"form": form})

        identificador = form.cleaned_data["identificador"]
        AutenticacaoService.solicitar_recuperacao_senha(
            identificador=identificador,
            ip=_obter_ip(request),
        )
        messages.success(request, "Código de verificação enviado")
        return redirect("contas:redefinir_senha")


class SenhaRedefinirView(View):
    def get(self, request):
        return render(
            request,
            "contas/redefinir_senha.html",
            {"form": RedefinirSenhaForm()},
        )

    def post(self, request):
        form = RedefinirSenhaForm(request.POST)
        if not form.is_valid():
            return render(request, "contas/redefinir_senha.html", {"form": form})

        dados = form.cleaned_data
        try:
            AutenticacaoService.redefinir_senha(
                identificador=dados["identificador"],
                codigo=dados["codigo"],
                nova_senha=dados["nova_senha"],
                ip=_obter_ip(request),
            )
        except TokenRecuperacaoInvalido as exc:
            form.add_error("codigo", str(exc))
            return render(request, "contas/redefinir_senha.html", {"form": form})

        messages.success(request, "Senha redefinida com sucesso")
        return redirect("contas:entrar")
