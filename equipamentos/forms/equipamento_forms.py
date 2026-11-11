from django import forms

from equipamentos.models import (
    AcaoDevolucaoEquipamento,
    TipoEquipamentoApoio,
)


class SolicitarEquipamentoForm(forms.Form):
    titular_cpf = forms.CharField(
        label="CPF do Beneficiário PCD",
        max_length=14,
        required=False,
    )
    tipo_equipamento = forms.ChoiceField(
        label="Categoria do Equipamento de Apoio",
        choices=TipoEquipamentoApoio.choices,
    )
    largura_quadril_cm = forms.IntegerField(
        label="Largura do Quadril (cm)",
        min_value=15,
        max_value=120,
    )
    altura_cm = forms.IntegerField(
        label="Estatura / Altura (cm)",
        min_value=40,
        max_value=240,
    )
    peso_kg = forms.DecimalField(
        label="Peso Corporal (kg)",
        min_value=5,
        max_value=300,
        max_digits=5,
        decimal_places=2,
    )
    observacoes_clinicas = forms.CharField(
        label="Observações Clínicas e Ergonômicas (máx. 500 caracteres)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    crm_medico = forms.CharField(
        label="CRM do Médico Emissor (opcional)",
        max_length=30,
        required=False,
    )
    data_emissao_laudo = forms.DateField(
        label="Data de Emissão do Laudo (opcional)",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    arquivo_laudo = forms.FileField(
        label="Laudo Médico Digitalizado (PDF, JPG ou PNG — máx. 10 MB)",
    )
    arquivo_comprovante_residencia = forms.FileField(
        label="Comprovante de Residência Atualizado (PDF, JPG ou PNG — máx. 5 MB)",
    )


class GerenciarPrazoEmprestimoForm(forms.Form):
    ACAO_CHOICES = [
        (
            AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA,
            "Solicitar Renovação de Prazo do Empréstimo",
        ),
        (
            AcaoDevolucaoEquipamento.DEVOLUCAO_CONFIRMADA,
            "Confirmar Devolução e Agendar Vistoria no Almoxarifado",
        ),
    ]

    acao = forms.ChoiceField(
        label="Ação sobre o Prazo do Empréstimo",
        choices=ACAO_CHOICES,
    )
    justificativa = forms.CharField(
        label="Justificativa Clínica (obrigatória para renovação)",
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

