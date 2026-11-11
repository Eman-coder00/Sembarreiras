import re

from django import forms
from django.core.exceptions import ValidationError

from contas.models import (
    GrauParentescoVinculo,
    PapelUsuario,
    TamanhoToque,
    TimeoutTela,
    TipoDeficiencia,
)
from contas.services import cpf_eh_valido, formatar_cep, formatar_cpf

OPCOES_EQUIPAMENTOS = [
    ("CADEIRA_MANUAL", "Cadeira de Rodas Manual"),
    ("CADEIRA_MOTORIZADA", "Cadeira Motorizada"),
    ("PROTESE", "Prótese"),
    ("MULETA_BENGALA", "Muleta / Bengala"),
    ("ANDADOR", "Andador"),
    ("NENHUM", "Nenhum"),
]


def validar_senha_alfanumerica(senha: str) -> str:
    if len(senha or "") < 8:
        raise ValidationError("A senha deve ter no mínimo 8 caracteres.")
    if not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise ValidationError("A senha deve conter letras e números.")
    return senha


def validar_telefone_nacional(telefone: str) -> str:
    digitos = re.sub(r"\D", "", telefone or "")
    if len(digitos) not in (10, 11):
        raise ValidationError("Informe um telefone válido com DDD.")
    ddd = int(digitos[:2])
    if ddd < 11 or ddd > 99:
        raise ValidationError("Informe um DDD nacional válido.")
    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"
    return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"


class CadastroPCDForm(forms.Form):
    cpf = forms.CharField(max_length=14, label="CPF")
    nome_completo = forms.CharField(min_length=3, max_length=120, label="Nome Completo")
    data_nascimento = forms.DateField(label="Data de Nascimento")
    telefone = forms.CharField(max_length=15, label="Telefone / WhatsApp")
    email = forms.EmailField(max_length=200, label="E-mail")
    senha = forms.CharField(widget=forms.PasswordInput, label="Senha (8+ dígitos)")
    tipo_deficiencia = forms.ChoiceField(
        choices=TipoDeficiencia.choices,
        label="Tipo de Deficiência Física",
    )
    equipamentos_apoio = forms.MultipleChoiceField(
        choices=OPCOES_EQUIPAMENTOS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Equipamento de Apoio Utilizado",
    )
    cep = forms.CharField(max_length=9, label="CEP")
    logradouro = forms.CharField(max_length=100, label="Logradouro")
    numero = forms.CharField(max_length=10, label="Número")
    complemento = forms.CharField(max_length=100, required=False, label="Complemento")
    bairro = forms.CharField(max_length=100, label="Bairro")
    municipio = forms.CharField(max_length=100, label="Município")
    uf = forms.CharField(min_length=2, max_length=2, label="UF")

    def clean_cpf(self) -> str:
        cpf = self.cleaned_data["cpf"]
        if not cpf_eh_valido(cpf):
            raise ValidationError("CPF inválido.")
        return formatar_cpf(cpf)

    def clean_telefone(self) -> str:
        return validar_telefone_nacional(self.cleaned_data["telefone"])

    def clean_senha(self) -> str:
        return validar_senha_alfanumerica(self.cleaned_data["senha"])

    def clean_cep(self) -> str:
        cep = self.cleaned_data["cep"]
        digitos = re.sub(r"\D", "", cep or "")
        if len(digitos) != 8:
            raise ValidationError("O CEP deve conter 8 dígitos.")
        return formatar_cep(cep)

    def clean_uf(self) -> str:
        return self.cleaned_data["uf"].strip().upper()


class LoginPerfilForm(forms.Form):
    perfil_selecionado = forms.ChoiceField(
        choices=PapelUsuario.choices,
        error_messages={
            "required": "Selecione o perfil de acesso",
            "invalid_choice": "Selecione o perfil de acesso",
        },
        label="Perfil de Acesso",
    )
    identificador = forms.CharField(
        max_length=200,
        label="Identificador de Acesso (E-mail ou CPF)",
    )
    senha = forms.CharField(
        widget=forms.PasswordInput,
        label="Senha",
    )
    manter_conectado = forms.BooleanField(
        required=False,
        label="Manter conectado",
    )


class CadastroCuidadorForm(forms.Form):
    cpf_cuidador = forms.CharField(max_length=14, label="CPF do Cuidador")
    nome_completo = forms.CharField(
        min_length=3,
        max_length=120,
        label="Nome Completo do Cuidador",
    )
    email = forms.EmailField(max_length=200, label="E-mail do Cuidador")
    telefone = forms.CharField(max_length=15, label="Telefone / WhatsApp")
    senha = forms.CharField(widget=forms.PasswordInput, label="Senha (8+ dígitos)")
    cpf_titular_pcd = forms.CharField(
        max_length=14,
        label="CPF do Usuário PCD Vinculado",
    )
    grau_parentesco = forms.ChoiceField(
        choices=GrauParentescoVinculo.choices,
        label="Grau de Parentesco / Vínculo",
    )

    def clean_cpf_cuidador(self) -> str:
        cpf = self.cleaned_data["cpf_cuidador"]
        if not cpf_eh_valido(cpf):
            raise ValidationError("CPF do cuidador inválido.")
        return formatar_cpf(cpf)

    def clean_cpf_titular_pcd(self) -> str:
        cpf = self.cleaned_data["cpf_titular_pcd"]
        if not cpf_eh_valido(cpf):
            raise ValidationError("CPF do titular PCD inválido.")
        return formatar_cpf(cpf)

    def clean_telefone(self) -> str:
        return validar_telefone_nacional(self.cleaned_data["telefone"])

    def clean_senha(self) -> str:
        return validar_senha_alfanumerica(self.cleaned_data["senha"])


class ConfirmarVinculoOTPForm(forms.Form):
    codigo_otp = forms.CharField(
        min_length=6,
        max_length=6,
        label="Código de Validação de Vínculo (OTP 6 dígitos)",
    )


class PerfilPCDEditarForm(forms.Form):
    nome_completo = forms.CharField(min_length=3, max_length=120, label="Nome Completo")
    telefone = forms.CharField(max_length=15, label="Telefone / WhatsApp")
    equipamentos_apoio = forms.MultipleChoiceField(
        choices=OPCOES_EQUIPAMENTOS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Equipamento de Apoio Utilizado",
    )
    cep = forms.CharField(max_length=9, label="CEP")
    logradouro = forms.CharField(max_length=100, label="Logradouro")
    numero = forms.CharField(max_length=10, label="Número")
    complemento = forms.CharField(max_length=100, required=False, label="Complemento")
    bairro = forms.CharField(max_length=100, label="Bairro")
    municipio = forms.CharField(max_length=100, label="Município")
    uf = forms.CharField(min_length=2, max_length=2, label="UF")
    senha_atual = forms.CharField(
        required=False,
        widget=forms.PasswordInput,
        label="Senha Atual (obrigatória ao alterar telefone ou endereço)",
    )

    def clean_telefone(self) -> str:
        return validar_telefone_nacional(self.cleaned_data["telefone"])

    def clean_cep(self) -> str:
        cep = self.cleaned_data["cep"]
        digitos = re.sub(r"\D", "", cep or "")
        if len(digitos) != 8:
            raise ValidationError("O CEP deve conter 8 dígitos.")
        return formatar_cep(cep)

    def clean_uf(self) -> str:
        return self.cleaned_data["uf"].strip().upper()


class AcessibilidadeMotoraForm(forms.Form):
    tipo_deficiencia = forms.ChoiceField(
        choices=TipoDeficiencia.choices,
        label="Tipo de Limitação Motora Configurada",
    )
    equipamentos_apoio = forms.MultipleChoiceField(
        choices=OPCOES_EQUIPAMENTOS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Equipamento de Mobilidade Utilizado",
    )
    tamanho_toque = forms.ChoiceField(
        choices=TamanhoToque.choices,
        label="Tamanho dos Componentes e Áreas de Toque",
    )
    timeout_tela = forms.ChoiceField(
        choices=TimeoutTela.choices,
        label="Tempo Limite de Sessão / Timeout",
    )
    alto_contraste = forms.BooleanField(
        required=False,
        label="Modo de Alto Contraste",
    )


class SolicitarRecuperacaoSenhaForm(forms.Form):
    identificador = forms.CharField(
        max_length=200,
        label="CPF ou E-mail cadastrado",
    )


class RedefinirSenhaForm(forms.Form):
    identificador = forms.CharField(max_length=200, label="CPF ou E-mail cadastrado")
    codigo = forms.CharField(
        min_length=6,
        max_length=6,
        label="Código de Recuperação (Token OTP 6 dígitos)",
    )
    nova_senha = forms.CharField(
        widget=forms.PasswordInput,
        label="Nova Senha (Mínimo 8 caracteres)",
    )
    confirmar_nova_senha = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirmar Nova Senha",
    )

    def clean_nova_senha(self) -> str:
        return validar_senha_alfanumerica(self.cleaned_data["nova_senha"])

    def clean(self):
        cleaned_data = super().clean() or {}
        nova = cleaned_data.get("nova_senha")
        confirmacao = cleaned_data.get("confirmar_nova_senha")
        if nova and confirmacao and nova != confirmacao:
            self.add_error(
                "confirmar_nova_senha",
                "A confirmação deve coincidir exatamente com a nova senha.",
            )
        return cleaned_data


class InativarContaForm(forms.Form):
    senha_atual = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirme sua senha para inativar a conta (LGPD)",
    )

