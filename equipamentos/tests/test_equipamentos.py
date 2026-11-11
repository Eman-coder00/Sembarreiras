import shutil
import tempfile
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contas.models import TipoDeficiencia, Usuario, VinculoCuidador
from contas.services import ContaService, VinculoCuidadorService
from equipamentos.exceptions import AnexoInvalido, OperacaoEmprestimoInvalida
from equipamentos.models import (
    AcaoDevolucaoEquipamento,
    StatusSolicitacaoEquipamento,
    TipoEquipamentoApoio,
)
from equipamentos.services import EquipamentoService

TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="sembarreiras_test_media_")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EquipamentosELaudosTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.beneficiario = ContaService.cadastrar_pcd(
            cpf="111.444.777-35",
            nome_completo="Fernanda Gomes",
            data_nascimento=date(1990, 11, 5),
            telefone="(82) 99933-4455",
            email="fernanda.pcd@adefal.org.br",
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
        self.staff = Usuario.objects.create_user(
            username="triagem_adefal",
            cpf="123.456.789-09",
            nome_completo="Equipe Técnica ADEFAL",
            email="triagem@adefal.org.br",
            password="SenhaForte@123",
            is_staff=True,
        )

    def _criar_pdf_valido(self, nome="laudo_medico.pdf", tamanho_bytes=120):
        conteudo = b"%PDF-1.4\n" + (b"0" * max(10, tamanho_bytes - 9))
        return SimpleUploadedFile(
            nome,
            conteudo,
            content_type="application/pdf",
        )

    def test_criar_solicitacao_valida_gera_protocolo_e_linha_do_tempo(self):
        solicitacao = EquipamentoService.criar_solicitacao(
            solicitante=self.beneficiario,
            tipo_equipamento=TipoEquipamentoApoio.CADEIRA_MOTORIZADA,
            largura_quadril_cm=46,
            altura_cm=168,
            peso_kg="68.50",
            arquivo_laudo=self._criar_pdf_valido("laudo.pdf"),
            arquivo_comprovante_residencia=self._criar_pdf_valido("comp.pdf"),
            observacoes_clinicas="Necessita apoio lateral de tronco.",
            crm_medico="CRM-AL 4589",
            data_emissao_laudo=date(2026, 10, 1),
        )
        self.assertTrue(solicitacao.protocolo.startswith("EQP-"))
        self.assertEqual(
            solicitacao.status, StatusSolicitacaoEquipamento.EM_ANALISE
        )
        _, eventos = EquipamentoService.obter_detalhe_e_linha_tempo(
            self.beneficiario, solicitacao.protocolo
        )
        self.assertEqual(eventos.count(), 1)

    def test_rejeita_extensao_invalida_ou_magic_bytes_adulterados(self):
        arquivo_exe = SimpleUploadedFile(
            "malware.exe",
            b"MZ\x90\x00",
            content_type="application/octet-stream",
        )
        with self.assertRaises(AnexoInvalido):
            EquipamentoService.validar_arquivo_anexo(
                arquivo_exe, tamanho_max_mb=10
            )

        pdf_falso = SimpleUploadedFile(
            "falso.pdf",
            b"#!/bin/sh\necho hack",
            content_type="application/pdf",
        )
        with self.assertRaises(AnexoInvalido):
            EquipamentoService.validar_arquivo_anexo(
                pdf_falso, tamanho_max_mb=10
            )

    def test_rejeita_arquivos_acima_do_limite_de_tamanho(self):
        comprovante_6mb = self._criar_pdf_valido(
            "grande.pdf", tamanho_bytes=6 * 1024 * 1024
        )
        with self.assertRaises(AnexoInvalido):
            EquipamentoService.validar_arquivo_anexo(
                comprovante_6mb, tamanho_max_mb=5
            )

    def test_download_protegido_de_laudo_medico_rs001(self):
        solicitacao = EquipamentoService.criar_solicitacao(
            solicitante=self.beneficiario,
            tipo_equipamento=TipoEquipamentoApoio.CADEIRA_MANUAL,
            largura_quadril_cm=44,
            altura_cm=165,
            peso_kg="65.00",
            arquivo_laudo=self._criar_pdf_valido("laudo.pdf"),
            arquivo_comprovante_residencia=self._criar_pdf_valido("comp.pdf"),
        )
        url_laudo = reverse(
            "equipamentos:baixar_anexo",
            args=[solicitacao.protocolo, "laudo"],
        )

        # Titular PCD baixa o anexo com sucesso
        self.client.force_login(self.beneficiario)
        resp_titular = self.client.get(url_laudo)
        self.assertEqual(resp_titular.status_code, 200)

        # Staff da ADEFAL baixa o anexo com sucesso
        self.client.force_login(self.staff)
        resp_staff = self.client.get(url_laudo)
        self.assertEqual(resp_staff.status_code, 200)

        # Cuidador com vínculo APROVADO baixa o anexo com sucesso
        vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
            cpf_cuidador="529.982.247-25",
            nome_completo="Paulo Cuidador",
            email="paulo.cuidador@adefal.org.br",
            telefone="(82) 98800-1122",
            senha="SenhaForte@123",
            cpf_titular_pcd=self.beneficiario.cpf,
            grau_parentesco="CONJUGE",
        )
        vinculo_db = VinculoCuidador.objects.get(pk=vinculo.id)
        VinculoCuidadorService.confirmar_vinculo(
            vinculo_id=vinculo.id,
            codigo_otp=vinculo_db.codigo_otp,
            solicitante=self.beneficiario,
        )
        self.client.force_login(vinculo.cuidador)
        resp_cuidador = self.client.get(url_laudo)
        self.assertEqual(resp_cuidador.status_code, 200)

        # Outro usuário autenticado sem vínculo recebe 404
        intruso = Usuario.objects.create_user(
            username="intruso",
            cpf="987.654.321-00",
            nome_completo="Intruso",
            email="intruso@adefal.org.br",
            password="SenhaForte@123",
        )
        self.client.force_login(intruso)
        resp_intruso = self.client.get(url_laudo)
        self.assertEqual(resp_intruso.status_code, 404)

    def test_evolucao_de_status_alertas_de_vencimento_e_renovacao(self):
        solicitacao = EquipamentoService.criar_solicitacao(
            solicitante=self.beneficiario,
            tipo_equipamento=TipoEquipamentoApoio.ANDADOR,
            largura_quadril_cm=42,
            altura_cm=160,
            peso_kg="60.00",
            arquivo_laudo=self._criar_pdf_valido("laudo.pdf"),
            arquivo_comprovante_residencia=self._criar_pdf_valido("comp.pdf"),
        )

        hoje = timezone.localdate()
        vencimento_2_dias = hoje + timedelta(days=2)

        EquipamentoService.atualizar_status_triagem(
            operador_staff=self.staff,
            protocolo=solicitacao.protocolo,
            novo_status=StatusSolicitacaoEquipamento.DEFERIDO_ENTREGUE,
            parecer_tecnico="Equipamento entregue no almoxarifado ADEFAL.",
            data_vencimento=vencimento_2_dias,
        )

        alertas = EquipamentoService.listar_alertas_vencimento(
            self.beneficiario, data_referencia=hoje
        )
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["nivel"], "URGENTE_2_DIAS")

        # Renovação sem justificativa deve falhar
        with self.assertRaises(OperacaoEmprestimoInvalida):
            EquipamentoService.registrar_renovacao_ou_devolucao(
                solicitante=self.beneficiario,
                protocolo=solicitacao.protocolo,
                acao=AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA,
                justificativa="",
            )

        # Renovação com justificativa funciona e registra na linha do tempo
        atualizada = EquipamentoService.registrar_renovacao_ou_devolucao(
            solicitante=self.beneficiario,
            protocolo=solicitacao.protocolo,
            acao=AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA,
            justificativa="Continuidade do tratamento fisioterápico pós-operatório.",
        )
        self.assertEqual(
            atualizada.acao_devolucao,
            AcaoDevolucaoEquipamento.RENOVACAO_SOLICITADA,
        )
        _, eventos = EquipamentoService.obter_detalhe_e_linha_tempo(
            self.beneficiario, solicitacao.protocolo
        )
        self.assertEqual(eventos.count(), 3)

