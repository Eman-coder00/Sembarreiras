from datetime import date

from django.test import TestCase
from django.urls import reverse

from contas.models import TipoDeficiencia, Usuario, VinculoCuidador
from contas.services import ContaService, VinculoCuidadorService
from emergencia.exceptions import (
    LimiteContatosExcedido,
    MinimoContatoAtivoObrigatorio,
    SemContatosDeEmergencia,
)
from emergencia.models import StatusOcorrenciaPanico
from emergencia.services import ContatoEmergenciaService, PanicoService


class EmergenciaServiceEViewsTest(TestCase):
    def setUp(self):
        self.titular = ContaService.cadastrar_pcd(
            cpf="111.444.777-35",
            nome_completo="Carlos Alberto Silva",
            data_nascimento=date(1988, 4, 12),
            telefone="(82) 99911-2233",
            email="carlos.pcd@adefal.org.br",
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

    def test_cadastro_ate_3_contatos_e_bloqueio_do_quarto(self):
        c1 = ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        c2 = ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="João Silva",
            telefone="(82) 99900-0002",
            parentesco="CUIDADOR",
            prioridade=2,
        )
        c3 = ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Ana Souza",
            telefone="(82) 99900-0003",
            parentesco="VIZINHO",
            prioridade=3,
        )
        self.assertEqual(
            list(ContatoEmergenciaService.listar_ativos(self.titular)),
            [c1, c2, c3],
        )

        with self.assertRaises(LimiteContatosExcedido):
            ContatoEmergenciaService.criar(
                titular_pcd=self.titular,
                nome="Quarto Contato",
                telefone="(82) 99900-0004",
                parentesco="AMIGO",
                prioridade=1,
            )

    def test_impede_excluir_unico_contato_ativo(self):
        contato = ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        with self.assertRaises(MinimoContatoAtivoObrigatorio):
            ContatoEmergenciaService.excluir(contato.id, self.titular)

    def test_acionar_panico_sem_contatos_ativos_eh_rejeitado(self):
        with self.assertRaises(SemContatosDeEmergencia):
            PanicoService.iniciar_acionamento(self.titular)

        self.client.force_login(self.titular)
        resposta = self.client.post(reverse("emergencia:panico"), follow=True)
        self.assertContains(
            resposta,
            "Cadastre ao menos 1 contato de emergência ativo antes de acionar o botão de pânico.",
        )

    def test_cancelar_alerta_na_contagem_regressiva(self):
        ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        self.client.force_login(self.titular)
        ocorrencia = PanicoService.iniciar_acionamento(
            self.titular, latitude=-9.6501, longitude=-35.7091
        )
        self.assertEqual(ocorrencia.status, StatusOcorrenciaPanico.EM_CONTAGEM)

        resposta = self.client.post(
            reverse("emergencia:cancelar", args=[ocorrencia.id]),
            follow=True,
        )
        self.assertContains(resposta, "Alerta cancelado com sucesso")

        ocorrencia.refresh_from_db()
        self.assertEqual(ocorrencia.status, StatusOcorrenciaPanico.CANCELADO)
        self.assertEqual(ocorrencia.contatos_notificados, "")
        self.assertEqual(ocorrencia.mensagem_enviada, "")

    def test_confirmar_disparo_grava_coordenadas_contatos_e_link(self):
        ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        ocorrencia = PanicoService.iniciar_acionamento(self.titular)
        disparada = PanicoService.confirmar_disparo(
            ocorrencia_id=ocorrencia.id,
            titular_pcd=self.titular,
            latitude=-9.64985,
            longitude=-35.70895,
            falha_dados=False,
        )
        self.assertEqual(disparada.status, StatusOcorrenciaPanico.ENTREGUE)
        self.assertIn("Maria Silva", disparada.contatos_notificados)
        self.assertIn(
            "EMERGÊNCIA! Preciso de ajuda imediata.",
            disparada.mensagem_enviada,
        )
        self.assertIn("https://maps.google.com/?q=", disparada.mensagem_enviada)

    def test_fallback_automatico_para_sms_quando_falha_dados(self):
        ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        ocorrencia = PanicoService.iniciar_acionamento(self.titular)
        disparada = PanicoService.confirmar_disparo(
            ocorrencia_id=ocorrencia.id,
            titular_pcd=self.titular,
            latitude=-9.64985,
            longitude=-35.70895,
            falha_dados=True,
        )
        self.assertEqual(disparada.status, StatusOcorrenciaPanico.FALLBACK_SMS)

    def test_historico_acessivel_por_cuidador_aprovado_e_bloqueado_sem_vinculo(self):
        ContatoEmergenciaService.criar(
            titular_pcd=self.titular,
            nome="Maria Silva",
            telefone="(82) 99900-0001",
            parentesco="FAMILIAR",
            prioridade=1,
        )
        ocorrencia = PanicoService.iniciar_acionamento(self.titular)
        PanicoService.confirmar_disparo(ocorrencia.id, self.titular)

        vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
            cpf_cuidador="529.982.247-25",
            nome_completo="Luciana Cuidadora",
            email="luciana.cuidadora@adefal.org.br",
            telefone="(82) 98877-6655",
            senha="SenhaForte@123",
            cpf_titular_pcd=self.titular.cpf,
            grau_parentesco="CUIDADOR_PROFISSIONAL",
        )
        cuidador = vinculo.cuidador

        # Antes de aprovar o vínculo, o acesso ao histórico deve retornar 404
        self.client.force_login(cuidador)
        resp_pendente = self.client.get(reverse("emergencia:historico"))
        self.assertEqual(resp_pendente.status_code, 404)

        # Após confirmar o OTP do vínculo, o cuidador visualiza o histórico
        vinculo_db = VinculoCuidador.objects.get(pk=vinculo.id)
        VinculoCuidadorService.confirmar_vinculo(
            vinculo_id=vinculo.id,
            codigo_otp=vinculo_db.codigo_otp,
            solicitante=self.titular,
        )

        resp_aprovado = self.client.get(reverse("emergencia:historico"))
        self.assertEqual(resp_aprovado.status_code, 200)
        self.assertContains(resp_aprovado, ocorrencia.codigo)

        # Outro usuário sem vínculo tentando consultar o CPF do titular recebe 404
        outro_usuario = Usuario.objects.create_user(
            username="outro_sem_vinculo",
            cpf="123.456.789-09",
            nome_completo="Outro Usuário",
            email="outro@adefal.org.br",
            password="SenhaForte@123",
            papel="CUIDADOR",
        )
        self.client.force_login(outro_usuario)
        resp_outro = self.client.get(reverse("emergencia:historico"))
        self.assertEqual(resp_outro.status_code, 404)

