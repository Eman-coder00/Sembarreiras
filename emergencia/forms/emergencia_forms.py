import re

from django import forms

from emergencia.models import (
    ParentescoContato,
    StatusContato,
    StatusOcorrenciaPanico,
)

DDDS_VALIDOS_BR = {
    "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "21", "22", "24", "27", "28",
    "31", "32", "33", "34", "35", "37", "38",
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "51", "53", "54", "55",
    "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "71", "73", "74", "75", "77", "79",
    "81", "82", "83", "84", "85", "86", "87", "88", "89",
    "91", "92", "93", "94", "95", "96", "97", "98", "99",
}


def validar_e_formatar_celular_br(valor: str) -> str:
    digitos = re.sub(r"\D", "", valor or "")
    if len(digitos) != 11 or digitos[2] != "9":
        raise forms.ValidationError(
            "Informe um celular válido no formato (XX) 9XXXX-XXXX."
        )
    ddd = digitos[:2]
    if ddd not in DDDS_VALIDOS_BR:
        raise forms.ValidationError("DDD inválido.")
    return f"({ddd}) {digitos[2:7]}-{digitos[7:]}"


class ContatoEmergenciaForm(forms.Form):
    PRIORIDADE_CHOICES = [
        (1, "1ª Prioridade (Principal)"),
        (2, "2ª Prioridade (Secundário)"),
        (3, "3ª Prioridade (Terciário)"),
    ]

    nome = forms.CharField(
        label="Nome do Contato",
        max_length=100,
        min_length=3,
    )
    telefone = forms.CharField(
        label="Telefone Celular ((XX) 9XXXX-XXXX)",
        max_length=15,
    )
    parentesco = forms.ChoiceField(
        label="Grau de Relação / Parentesco",
        choices=ParentescoContato.choices,
        initial=ParentescoContato.FAMILIAR,
    )
    prioridade = forms.TypedChoiceField(
        label="Ordem de Prioridade no Disparo",
        choices=PRIORIDADE_CHOICES,
        coerce=int,
        initial=1,
    )
    status = forms.TypedChoiceField(
        label="Status do Contato",
        choices=StatusContato.choices,
        coerce=int,
        initial=StatusContato.ATIVO,
        required=False,
    )

    def clean_nome(self) -> str:
        nome = (self.cleaned_data.get("nome") or "").strip()
        if len(nome) < 3:
            raise forms.ValidationError(
                "O nome do contato deve ter pelo menos 3 caracteres."
            )
        return nome

    def clean_telefone(self) -> str:
        return validar_e_formatar_celular_br(
            self.cleaned_data.get("telefone", "")
        )

    def clean_status(self) -> int:
        valor = self.cleaned_data.get("status")
        return int(valor) if valor else int(StatusContato.ATIVO)


class AcionarPanicoForm(forms.Form):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)


class DispararPanicoForm(forms.Form):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    falha_dados = forms.BooleanField(
        label="Simular ausência de dados móveis (Fallback SMS nativo)",
        required=False,
    )


class FiltroHistoricoPanicoForm(forms.Form):
    STATUS_FILTRO_CHOICES = [("", "Todos os status")] + list(
        StatusOcorrenciaPanico.choices
    )

    titular_cpf = forms.CharField(
        label="CPF do Titular PCD",
        max_length=14,
        required=False,
    )
    data_inicio = forms.DateField(
        label="Data inicial",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    data_fim = forms.DateField(
        label="Data final",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    status = forms.ChoiceField(
        label="Status da Ocorrência",
        choices=STATUS_FILTRO_CHOICES,
        required=False,
    )

