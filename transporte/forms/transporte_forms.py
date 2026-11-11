from django import forms


class FiltroLinhasAcessiveisForm(forms.Form):
    RAIO_CHOICES = [
        (500, "Até 500 metros"),
        (1000, "Até 1 km"),
        (2000, "Até 2 km (Padrão)"),
        (5000, "Até 5 km (Região Metropolitana)"),
        (15000, "Toda Maceió (15 km)"),
    ]

    origem = forms.CharField(
        label="Ponto de Embarque / Bairro de Origem",
        max_length=100,
        required=False,
    )
    linha = forms.CharField(
        label="Código da Linha ou Destino (ex.: 051, ADEFAL, Farol)",
        max_length=100,
        required=False,
    )
    raio = forms.TypedChoiceField(
        label="Raio de Proximidade do Ponto",
        choices=RAIO_CHOICES,
        coerce=int,
        initial=5000,
        required=False,
    )
    lat = forms.FloatField(required=False, widget=forms.HiddenInput())
    lon = forms.FloatField(required=False, widget=forms.HiddenInput())


class FiltroMapaAcessivelForm(forms.Form):
    busca = forms.CharField(
        label="Buscar por Bairro, Ponto de Parada ou Sede ADEFAL",
        max_length=100,
        required=False,
    )
