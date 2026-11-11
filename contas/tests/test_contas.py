from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contas.exceptions import (
    CepNaoLocalizado,
    ContaTemporariamenteBloqueada,
    CpfJaCadastrado,
    CredenciaisInvalidas,
    EmailJaCadastrado,
    PermissaoNegadaTitular,
    SenhaAtualInvalida,
    TokenRecuperacaoInvalido,
    VinculoInvalido,
)
from contas.models import (
    CepLocal,
    GrauParentescoVinculo,
    LogAuditoriaConta,
    PapelUsuario,
    StatusCadastro,
    StatusVinculo,
    TamanhoToque,
    TimeoutTela,
    TipoDeficiencia,
    TokenRecuperacaoSenha,
    Usuario,
)
from contas.services import (
    AutenticacaoService,
    ContaService,
    VinculoCuidadorService,
)

CPF_PCD_VALIDO = "529.982.247-25"
CPF_CUIDADOR_VALIDO = "111.444.777-35"
CPF_OUTRO_VALIDO = "123.456.789-09"


class ContasServiceEViewsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        CepLocal.objects.create(
            cep="57051-120",
            logradouro="Av. Fernandes Lima",
            bairro="Farol",
            municipio="Maceió",
            uf="AL",
        )
        cls.titular = ContaService.cadastrar_pcd(
            cpf=CPF_PCD_VALIDO,
            nome_completo="João da Silva Ramos",
            data_nascimento=date(1992, 8, 14),
            telefone="(82) 99876-5432",
            email="joao.silva@email.com",
            senha="Password123",
            tipo_deficiencia=TipoDeficiencia.CADEIRANTE,
            equipamentos_apoio=["CADEIRA_MOTORIZADA"],
            cep="57051-120",
            logradouro="Av. Fernandes Lima",
            numero="450",
            complemento="Ap 101",
            bairro="Farol",
            municipio="Maceió",
            uf="AL",
        )

    def test_cadastro_pcd_rejeita_cpf_ou_email_duplicado(self):
        with self.assertRaises(CpfJaCadastrado):
            ContaService.cadastrar_pcd(
                cpf=CPF_PCD_VALIDO,
                nome_completo="Outro Nome",
                data_nascimento=date(1990, 1, 1),
                telefone="(82) 99876-5432",
                email="outro@email.com",
                senha="Password123",
                tipo_deficiencia=TipoDeficiencia.CADEIRANTE,
                equipamentos_apoio=["CADEIRA_MANUAL"],
                cep="57051-120",
                logradouro="Av. Fernandes Lima",
                numero="10",
                bairro="Farol",
                municipio="Maceió",
                uf="AL",
            )

        with self.assertRaises(EmailJaCadastrado):
            ContaService.cadastrar_pcd(
                cpf=CPF_OUTRO_VALIDO,
                nome_completo="Outro Nome",
                data_nascimento=date(1990, 1, 1),
                telefone="(82) 99876-5432",
                email="joao.silva@email.com",
                senha="Password123",
                tipo_deficiencia=TipoDeficiencia.CADEIRANTE,
                equipamentos_apoio=["CADEIRA_MANUAL"],
                cep="57051-120",
                logradouro="Av. Fernandes Lima",
                numero="10",
                bairro="Farol",
                municipio="Maceió",
                uf="AL",
            )

    def test_consulta_cep_existente_e_inexistente(self):
        dados = ContaService.consultar_cep("57051120")
        self.assertEqual(dados["logradouro"], "Av. Fernandes Lima")
        self.assertEqual(dados["bairro"], "Farol")

        with self.assertRaises(CepNaoLocalizado):
            ContaService.consultar_cep("99999-999")

        resp_ok = self.client.get(
            reverse("contas:consultar_cep"), {"cep": "57051-120"}
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertTrue(resp_ok.json()["encontrado"])

        resp_404 = self.client.get(
            reverse("contas:consultar_cep"), {"cep": "99999-999"}
        )
        self.assertEqual(resp_404.status_code, 404)
        self.assertEqual(resp_404.json()["mensagem"], "Endereço não localizado")

    def test_login_aceita_cpf_ou_email_e_valida_perfil(self):
        usuario_por_cpf = AutenticacaoService.autenticar(
            identificador=CPF_PCD_VALIDO,
            senha="Password123",
            perfil_selecionado=PapelUsuario.PCD,
        )
        self.assertEqual(usuario_por_cpf, self.titular)

        usuario_por_email = AutenticacaoService.autenticar(
            identificador="JOAO.SILVA@EMAIL.COM",
            senha="Password123",
            perfil_selecionado=PapelUsuario.PCD,
        )
        self.assertEqual(usuario_por_email, self.titular)

        with self.assertRaises(CredenciaisInvalidas):
            AutenticacaoService.autenticar(
                identificador=CPF_PCD_VALIDO,
                senha="Password123",
                perfil_selecionado=PapelUsuario.CUIDADOR,
            )

    def test_cinco_tentativas_incorretas_bloqueiam_conta_por_15_minutos(self):
        for _ in range(4):
            with self.assertRaises(CredenciaisInvalidas):
                AutenticacaoService.autenticar(
                    identificador=CPF_PCD_VALIDO,
                    senha="SenhaErrada1",
                    perfil_selecionado=PapelUsuario.PCD,
                )

        with self.assertRaises(ContaTemporariamenteBloqueada):
            AutenticacaoService.autenticar(
                identificador=CPF_PCD_VALIDO,
                senha="SenhaErrada1",
                perfil_selecionado=PapelUsuario.PCD,
            )

        # Mesmo com a senha certa, continua bloqueado durante os 15 minutos
        with self.assertRaises(ContaTemporariamenteBloqueada):
            AutenticacaoService.autenticar(
                identificador=CPF_PCD_VALIDO,
                senha="Password123",
                perfil_selecionado=PapelUsuario.PCD,
            )

    def test_ciclo_completo_de_vinculo_cuidador_com_otp_e_revogacao(self):
        vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
            cpf_cuidador=CPF_CUIDADOR_VALIDO,
            nome_completo="Maria Silva Ramos",
            email="maria.cuidadora@email.com",
            telefone="(82) 98877-6655",
            senha="Password123",
            cpf_titular_pcd=CPF_PCD_VALIDO,
            grau_parentesco=GrauParentescoVinculo.MAE_PAI,
        )
        self.assertEqual(vinculo.status, StatusVinculo.PENDENTE)

        # Enquanto pendente, cuidador não tem permissão sobre o titular
        with self.assertRaises(PermissaoNegadaTitular):
            ContaService.obter_titular_autorizado(vinculo.cuidador)

        # Código OTP incorreto é rejeitado
        with self.assertRaises(VinculoInvalido):
            VinculoCuidadorService.confirmar_vinculo(
                vinculo_id=vinculo.pk,
                codigo_otp="000000",
                solicitante=self.titular,
            )

        # Código OTP correto aprova o vínculo
        vinculo = VinculoCuidadorService.confirmar_vinculo(
            vinculo_id=vinculo.pk,
            codigo_otp=vinculo.codigo_otp,
            solicitante=self.titular,
        )
        self.assertEqual(vinculo.status, StatusVinculo.APROVADO)
        self.assertEqual(
            ContaService.obter_titular_autorizado(vinculo.cuidador),
            self.titular,
        )

        # Revogação retira o acesso imediatamente
        VinculoCuidadorService.revogar_vinculo(
            vinculo_id=vinculo.pk,
            solicitante=self.titular,
        )
        with self.assertRaises(PermissaoNegadaTitular):
            ContaService.obter_titular_autorizado(vinculo.cuidador)

    def test_acessibilidade_motora_aplica_classes_wcag_no_template(self):
        self.client.force_login(self.titular)
        resp = self.client.post(
            reverse("contas:acessibilidade"),
            {
                "tipo_deficiencia": TipoDeficiencia.CADEIRANTE,
                "equipamentos_apoio": ["CADEIRA_MOTORIZADA"],
                "tamanho_toque": TamanhoToque.MAXIMO,
                "timeout_tela": TimeoutTela.PROLONGADO_10M,
                "alto_contraste": "on",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "toque-maximo")
        self.assertContains(resp, "alto-contraste")
        self.assertContains(
            resp, "Perfil de acessibilidade atualizado com sucesso"
        )

    def test_alteracao_de_telefone_ou_endereco_exige_senha_atual_e_auditoria(self):
        with self.assertRaises(SenhaAtualInvalida):
            ContaService.atualizar_dados_pcd(
                self.titular,
                nome_completo="João da Silva Ramos",
                telefone="(82) 99111-2222",
                equipamentos_apoio=["CADEIRA_MOTORIZADA"],
                cep="57051-120",
                logradouro="Av. Fernandes Lima",
                numero="450",
                bairro="Farol",
                municipio="Maceió",
                uf="AL",
                senha_atual="",
            )

        ContaService.atualizar_dados_pcd(
            self.titular,
            nome_completo="João da Silva Ramos",
            telefone="(82) 99111-2222",
            equipamentos_apoio=["CADEIRA_MOTORIZADA"],
            cep="57051-120",
            logradouro="Av. Fernandes Lima",
            numero="500",
            bairro="Farol",
            municipio="Maceió",
            uf="AL",
            senha_atual="Password123",
            ip="127.0.0.1",
        )
        self.titular.refresh_from_db()
        self.assertEqual(self.titular.cpf, CPF_PCD_VALIDO)
        self.assertTrue(
            LogAuditoriaConta.objects.filter(
                usuario=self.titular,
                evento="ALTERACAO_DADOS_CRITICOS",
            ).exists()
        )

    def test_recuperacao_e_redefinicao_de_senha_com_expiracao(self):
        token = AutenticacaoService.solicitar_recuperacao_senha(
            identificador=CPF_PCD_VALIDO
        )
        self.assertIsNotNone(token)
        assert token is not None

        with self.assertRaises(TokenRecuperacaoInvalido):
            AutenticacaoService.redefinir_senha(
                identificador=CPF_PCD_VALIDO,
                codigo="000000",
                nova_senha="NovaPassword99",
            )

        AutenticacaoService.redefinir_senha(
            identificador=CPF_PCD_VALIDO,
            codigo=token.codigo,
            nova_senha="NovaPassword99",
        )
        self.titular.refresh_from_db()
        self.assertTrue(self.titular.check_password("NovaPassword99"))

        # Reutilizar o mesmo token deve falhar
        with self.assertRaises(TokenRecuperacaoInvalido):
            AutenticacaoService.redefinir_senha(
                identificador=CPF_PCD_VALIDO,
                codigo=token.codigo,
                nova_senha="OutraPassword88",
            )

        # Token expirado (> 15 min) deve falhar
        token_expirado = AutenticacaoService.solicitar_recuperacao_senha(
            identificador=CPF_PCD_VALIDO
        )
        assert token_expirado is not None
        TokenRecuperacaoSenha.objects.filter(pk=token_expirado.pk).update(
            expira_em=timezone.now() - timedelta(minutes=1)
        )
        with self.assertRaises(TokenRecuperacaoInvalido):
            AutenticacaoService.redefinir_senha(
                identificador=CPF_PCD_VALIDO,
                codigo=token_expirado.codigo,
                nova_senha="OutraPassword88",
            )

    def test_inativacao_logica_lgpd_mascara_dados_e_impede_login(self):
        ContaService.inativar_conta_lgpd(
            self.titular,
            senha_atual="Password123",
            ip="127.0.0.1",
        )
        self.titular.refresh_from_db()
        self.assertEqual(self.titular.status_cadastro, StatusCadastro.INATIVO)
        self.assertFalse(self.titular.is_active)
        self.assertIn("Titular Anonimizado", self.titular.nome_completo)
        self.assertTrue(
            Usuario.objects.filter(pk=self.titular.pk).exists(),
            "O registro não deve sofrer exclusão física.",
        )

        with self.assertRaises(CredenciaisInvalidas):
            AutenticacaoService.autenticar(
                identificador=CPF_PCD_VALIDO,
                senha="Password123",
                perfil_selecionado=PapelUsuario.PCD,
            )

    def test_home_adapta_grade_de_botoes_por_perfil_pcd_e_cuidador(self):
        self.client.force_login(self.titular)
        resp_pcd = self.client.get(reverse("contas:home"))
        self.assertEqual(resp_pcd.status_code, 200)
        self.assertContains(resp_pcd, "Botão de")
        self.assertContains(resp_pcd, "Ajustes de")

        vinculo = VinculoCuidadorService.cadastrar_cuidador_e_solicitar_vinculo(
            cpf_cuidador=CPF_CUIDADOR_VALIDO,
            nome_completo="Maria Cuidadora",
            email="maria.home@email.com",
            telefone="(82) 98877-6655",
            senha="Password123",
            cpf_titular_pcd=CPF_PCD_VALIDO,
            grau_parentesco=GrauParentescoVinculo.MAE_PAI,
        )
        self.client.force_login(vinculo.cuidador)
        resp_cuidador = self.client.get(reverse("contas:home"))
        self.assertEqual(resp_cuidador.status_code, 200)
        self.assertContains(resp_cuidador, "Minha Conta")
        self.assertNotContains(resp_cuidador, "Ajustes de<br>Acessibilidade")

