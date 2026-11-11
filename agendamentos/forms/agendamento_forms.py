from django import forms

from agendamentos.models import (
    EquipamentoTransporteHospitalar,
    EspecialidadeADEFAL,
    StatusConsulta,
    UnidadeADEFAL,
)


class FiltroVagasADEFALForm(forms.Form):
    ESPECIALIDADE_CHOICES = [("", "Todas as especialidades")] + list(
        EspecialidadeADEFAL.choices
    )
    UNIDADE_CHOICES = [("", "Todas as unidades")] + list(
        UnidadeADEFAL.choices
    )

    especialidade = forms.ChoiceField(
        label="Especialidade Clínica / Reabilitação",
        choices=ESPECIALIDADE_CHOICES,
        required=False,
    )
    unidade = forms.ChoiceField(
        label="Unidade ADEFAL",
        choices=UNIDADE_CHOICES,
        required=False,
    )
    data = forms.DateField(
        label="Data desejada",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )


class AgendarConsultaForm(forms.Form):
    vaga_id = forms.IntegerField(
        label="Horário disponível",
        min_value=1,
    )
    titular_cpf = forms.CharField(
        label="CPF do Titular PCD",
        max_length=14,
        required=False,
    )


class FiltroMeusAgendamentosForm(forms.Form):
    STATUS_CHOICES = [("", "Todos os status")] + list(StatusConsulta.choices)

    titular_cpf = forms.CharField(
        label="CPF do Titular PCD",
        max_length=14,
        required=False,
    )
    status = forms.ChoiceField(
        label="Status da Consulta",
        choices=STATUS_CHOICES,
        required=False,
    )


class CancelarConsultaForm(forms.Form):
    justificativa = forms.CharField(
        label="Motivo do cancelamento",
        max_length=200,
        required=False,
    )


class RemarcarConsultaForm(forms.Form):
    nova_vaga_id = forms.IntegerField(
        label="Novo horário disponível",
        min_value=1,
    )
    justificativa = forms.CharField(
        label="Motivo da remarcação",
        max_length=200,
        required=False,
    )


class SolicitarTransporteHospitalarForm(forms.Form):
    endereco_embarque = forms.CharField(
        label="Endereço Completo de Embarque (Porta a Porta)",
        max_length=250,
    )
    equipamento_transporte = forms.ChoiceField(
        label="Recurso de Locomoção para Embarque na Van",
        choices=EquipamentoTransporteHospitalar.choices,
        initial=EquipamentoTransporteHospitalar.CADEIRA_MANUAL,
    )
    precisa_acompanhante = forms.BooleanField(
        label="Necessita de assento adicional para acompanhante / cuidador",
        required=False,
    )


class ValidarComprovanteQRForm(forms.Form):
    protocolo = forms.CharField(
        label="Protocolo da Consulta (ex.: CNS-20261110-1234)",
        max_length=24,
    )
    assinatura = forms.CharField(
        label="Assinatura Criptográfica HMAC-SHA256 do QR Code",
        max_length=64,
    )

