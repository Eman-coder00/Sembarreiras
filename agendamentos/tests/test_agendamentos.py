from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agendamentos.exceptions import (
    ComprovanteInvalido,
    PrazoMinimo24hConsulta,
    PrazoMinimo48hTransporte,
    SemVagaFrotaAdaptada,
    VagaIndisponivel,
)
from agendamentos.models import (
    EquipamentoTransporteHospitalar,
    EspecialidadeADEFAL,
    StatusConsulta,
    StatusTransporteHospitalar,
    UnidadeADEFAL,
    VagaAgendaADEFAL,
    VagaFrotaAdaptada,
)
from agendamentos.services import (
    AgendamentoService,
    ComprovanteService,
    TransporteHospitalarService,
)
from contas.models import TipoDeficiencia, Usuario, VinculoCuidador
from contas.services import ContaService, VinculoCuidadorService


class AgendamentosETransporteHospitalarTest(TestCase):
    def setUp(self):
        self.paciente = ContaService.cadastrar_pcd(
            cpf="111.444.777-35",
            nome_completo="Roberto Nascimento",
            data_nascimento=date(1985, 9, 20),
            telefone="(82) 99988-7766",
            email="roberto.pcd@adefal.org.br",
            senha="SenhaForte@123",
            tipo_deficiencia=TipoDeficiencia.CADEIRANTE,
            equipamentos_apoio=["CADEIRA_MANUAL"],
            cep="57051-190",
            logradouro="Rua Clementino do Monte",
            numero="225",
            bairro="Farol",
            municipio="Maceió",
            uf="AL",
        )

        hoje = timezone.localdate()
        self.data_futura_5d = hoje + timedelta(days=5)
        self.data_futura_6d = hoje + timedelta(days=6)

        self.vaga_5d = VagaAgendaADEFAL.objects.create(
            especialidade=EspecialidadeADEFAL.FISIOTERAPIA,
            unidade=UnidadeADEFAL.SEDE_MACEIO,
            profissional="Dra. Camila Rocha",
            data=self.data_futura_5d,
            horario=time(9, 0),
            disponivel=True,
        )
        self.vaga_6d = VagaAgendaADEFAL.objects.create(
            especialidade=EspecialidadeADEFAL.FISIOTERAPIA,
            unidade=UnidadeADEFAL.SEDE_MACEIO,
            profissional="Dra. Camila Rocha",
            data=self.data_futura_6d,
            horario=time(10, 0),
            disponivel=True,
        )

        self.frota_5d = VagaFrotaAdaptada.objects.create(
            data=self.data_futura_5d,
            turno_horario=time(8, 0),
            veiculo_identificacao="Van Adaptada ADEFAL 01",
            motorista="José Carlos",
            vagas_cadeirante_total=2,
            vagas_cadeirante_ocupadas=0,
        )

    def test_agendar_gera_protocolo_ocupa_vaga_e_impede_duplicidade(self):
        consulta = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=self.vaga_5d.id,
        )
        self.assertTrue(consulta.protocolo.startswith("CNS-"))
        self.vaga_5d.refresh_from_db()
        self.assertFalse(self.vaga_5d.disponivel)

        with self.assertRaises(VagaIndisponivel):
            AgendamentoService.agendar(
                solicitante=self.paciente,
                vaga_id=self.vaga_5d.id,
            )

    def test_cancelar_e_remarcar_com_mais_de_24h_libera_vaga_e_transporte(self):
        consulta = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=self.vaga_5d.id,
        )
        transporte = TransporteHospitalarService.solicitar_transporte(
            solicitante=self.paciente,
            protocolo_consulta=consulta.protocolo,
            endereco_embarque="Rua Clementino do Monte, 225 - Farol",
            precisa_acompanhante=True,
            equipamento_transporte=EquipamentoTransporteHospitalar.CADEIRA_MANUAL,
        )
        self.frota_5d.refresh_from_db()
        self.assertEqual(self.frota_5d.vagas_cadeirante_ocupadas, 1)

        nova_consulta = AgendamentoService.remarcar(
            solicitante=self.paciente,
            protocolo=consulta.protocolo,
            nova_vaga_id=self.vaga_6d.id,
            justificativa="Mudança de turno",
        )
        self.assertEqual(nova_consulta.status, StatusConsulta.CONFIRMADO)
        self.vaga_5d.refresh_from_db()
        self.assertTrue(self.vaga_5d.disponivel)

        transporte.refresh_from_db()
        self.assertEqual(
            transporte.status, StatusTransporteHospitalar.CANCELADO
        )
        self.frota_5d.refresh_from_db()
        self.assertEqual(self.frota_5d.vagas_cadeirante_ocupadas, 0)

    def test_bloqueia_cancelamento_faltando_menos_de_24h(self):
        agora = timezone.now()
        dt_proxima = agora + timedelta(hours=12)
        vaga_curta = VagaAgendaADEFAL.objects.create(
            especialidade=EspecialidadeADEFAL.ORTOPEDIA,
            unidade=UnidadeADEFAL.SEDE_MACEIO,
            profissional="Dr. Marcos Lima",
            data=dt_proxima.date(),
            horario=dt_proxima.time().replace(second=0, microsecond=0),
            disponivel=True,
        )
        consulta = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=vaga_curta.id,
        )
        with self.assertRaises(PrazoMinimo24hConsulta):
            AgendamentoService.cancelar(
                solicitante=self.paciente,
                protocolo=consulta.protocolo,
            )

    def test_solicitar_transporte_exige_48h_e_vaga_na_frota(self):
        agora = timezone.now()
        dt_30h = agora + timedelta(hours=30)
        vaga_30h = VagaAgendaADEFAL.objects.create(
            especialidade=EspecialidadeADEFAL.NEUROLOGIA,
            unidade=UnidadeADEFAL.SEDE_MACEIO,
            profissional="Dra. Helena Costa",
            data=dt_30h.date(),
            horario=dt_30h.time().replace(second=0, microsecond=0),
            disponivel=True,
        )
        consulta_30h = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=vaga_30h.id,
        )
        with self.assertRaises(PrazoMinimo48hTransporte):
            TransporteHospitalarService.solicitar_transporte(
                solicitante=self.paciente,
                protocolo_consulta=consulta_30h.protocolo,
                endereco_embarque="Rua A, 10",
                precisa_acompanhante=False,
                equipamento_transporte=EquipamentoTransporteHospitalar.CADEIRA_MANUAL,
            )

        # Testa falta de vaga na frota
        self.frota_5d.vagas_cadeirante_ocupadas = 2
        self.frota_5d.save()
        consulta_5d = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=self.vaga_5d.id,
        )
        with self.assertRaises(SemVagaFrotaAdaptada):
            TransporteHospitalarService.solicitar_transporte(
                solicitante=self.paciente,
                protocolo_consulta=consulta_5d.protocolo,
                endereco_embarque="Rua A, 10",
                precisa_acompanhante=False,
                equipamento_transporte=EquipamentoTransporteHospitalar.CADEIRA_MANUAL,
            )

    def test_comprovante_digital_e_validacao_hmac_na_portaria(self):
        consulta = AgendamentoService.agendar(
            solicitante=self.paciente,
            vaga_id=self.vaga_5d.id,
        )
        validada = ComprovanteService.validar_comprovante(
            protocolo=consulta.protocolo,
            assinatura=consulta.assinatura_qr,
        )
        self.assertEqual(validada.id, consulta.id)

        with self.assertRaises(ComprovanteInvalido):
            ComprovanteService.validar_comprovante(
                protocolo=consulta.protocolo,
                assinatura="0" * 64,
            )

        staff = Usuario.objects.create_user(
            username="portaria_adefal",
            cpf="123.456.789-09",
            nome_completo="Portaria ADEFAL",
            email="portaria@adefal.org.br",
            password="SenhaForte@123",
            is_staff=True,
        )
        self.client.force_login(staff)
        resp = self.client.post(
            reverse("agendamentos:validar_qr"),
            {
                "protocolo": consulta.protocolo,
                "assinatura": consulta.assinatura_qr,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Comprovante autêntico!")

    def test_cuidador_aprovado_agenda_e_visualiza_consulta_do_titular(self):
        vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
            cpf_cuidador="529.982.247-25",
            nome_completo="Marcos Cuidador",
            email="marcos.cuidador@adefal.org.br",
            telefone="(82) 98811-2233",
            senha="SenhaForte@123",
            cpf_titular_pcd=self.paciente.cpf,
            grau_parentesco="MAE_PAI",
        )
        vinculo_db = VinculoCuidador.objects.get(pk=vinculo.id)
        VinculoCuidadorService.confirmar_vinculo(
            vinculo_id=vinculo.id,
            codigo_otp=vinculo_db.codigo_otp,
            solicitante=self.paciente,
        )

        cuidador = vinculo.cuidador
        consulta = AgendamentoService.agendar(
            solicitante=cuidador,
            vaga_id=self.vaga_5d.id,
            titular_cpf=self.paciente.cpf,
        )
        self.client.force_login(cuidador)
        resp = self.client.get(
            reverse("agendamentos:detalhe", args=[consulta.protocolo])
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, consulta.protocolo)

