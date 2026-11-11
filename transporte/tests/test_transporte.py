from datetime import date

from django.test import TestCase
from django.urls import reverse

from contas.models import TipoDeficiencia
from contas.services import ContaService
from transporte.models import (
    LinhaOnibus,
    PontoParada,
    TipoEquipamentoOnibus,
    VeiculoAdaptado,
)
from transporte.services import TransporteUrbanoService


class TransporteUrbanoTest(TestCase):
    def setUp(self):
        self.usuario = ContaService.cadastrar_pcd(
            cpf="111.444.777-35",
            nome_completo="Marina Oliveira",
            data_nascimento=date(1992, 6, 15),
            telefone="(82) 99912-3456",
            email="marina.pcd@adefal.org.br",
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

        self.linha_farol = LinhaOnibus.objects.create(
            codigo="051",
            nome="Santos Dumont / Trapiche (Via Farol - ADEFAL)",
            itinerario="Santos Dumont, Farol, Sede ADEFAL, Centro, Trapiche da Barra",
            ativa=True,
        )
        self.linha_pajucara = LinhaOnibus.objects.create(
            codigo="704",
            nome="Benedito Bentes / Ponta Verde",
            itinerario="Benedito Bentes, Farol, Pajuçara, Ponta Verde",
            ativa=True,
        )

        self.ponto_adefal = PontoParada.objects.create(
            nome="Parada ADEFAL Farol",
            logradouro="Rua Clementino do Monte, 225",
            bairro="Farol",
            latitude=-9.64985,
            longitude=-35.70895,
        )
        self.ponto_adefal.linhas.add(self.linha_farol, self.linha_pajucara)

        self.veiculo_acessivel = VeiculoAdaptado.objects.create(
            prefixo="MCZ-1042",
            linha=self.linha_farol,
            acessibilidade_ativa=True,
            tipo_equipamento=TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
            vagas_cadeirante=2,
            latitude_atual=-9.64500,
            longitude_atual=-35.70500,
            velocidade_media_kmh=24.0,
        )
        self.veiculo_inoperante = VeiculoAdaptado.objects.create(
            prefixo="MCZ-9999",
            linha=self.linha_farol,
            acessibilidade_ativa=False,
            tipo_equipamento=TipoEquipamentoOnibus.ELEVADOR_HIDRAULICO,
            vagas_cadeirante=1,
            latitude_atual=-9.64800,
            longitude_atual=-35.70800,
            velocidade_media_kmh=25.0,
        )

    def test_busca_retorna_apenas_veiculos_com_acessibilidade_ativa(self):
        resultados = TransporteUrbanoService.buscar_veiculos_acessiveis(
            raio_metros=5000
        )
        prefixos = [r["veiculo"].prefixo for r in resultados]
        self.assertIn("MCZ-1042", prefixos)
        self.assertNotIn("MCZ-9999", prefixos)

    def test_filtro_por_linha_e_origem(self):
        VeiculoAdaptado.objects.create(
            prefixo="MCZ-2088",
            linha=self.linha_pajucara,
            acessibilidade_ativa=True,
            tipo_equipamento=TipoEquipamentoOnibus.RAMPA_ACESSIVEL,
            vagas_cadeirante=1,
            latitude_atual=-9.64700,
            longitude_atual=-35.70700,
            velocidade_media_kmh=25.0,
        )
        filtrados = TransporteUrbanoService.buscar_veiculos_acessiveis(
            origem_texto="Farol",
            linha_termo="051",
            raio_metros=5000,
        )
        self.assertEqual(len(filtrados), 1)
        self.assertEqual(filtrados[0]["veiculo"].prefixo, "MCZ-1042")

    def test_calcular_eta_minutos_consistente(self):
        distancia_m, eta_min = TransporteUrbanoService.calcular_eta_minutos(
            lat_veiculo=-9.64500,
            lon_veiculo=-35.70500,
            lat_ponto=-9.64985,
            lon_ponto=-35.70895,
            velocidade_kmh=24.0,
        )
        self.assertGreater(distancia_m, 400)
        self.assertLess(distancia_m, 1000)
        self.assertGreaterEqual(eta_min, 1)

    def test_rastrear_veiculo_exibe_eta_e_retorna_404_para_inoperante(self):
        self.client.force_login(self.usuario)
        resp_ok = self.client.get(
            reverse("transporte:rastrear", args=["MCZ-1042"])
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertContains(
            resp_ok,
            "Próximo ônibus adaptado chega em aproximadamente",
        )

        resp_inop = self.client.get(
            reverse("transporte:rastrear", args=["MCZ-9999"])
        )
        self.assertEqual(resp_inop.status_code, 404)

    def test_mapa_acessivel_lista_pontos_de_parada_e_veiculos_ativos(self):
        self.client.force_login(self.usuario)
        resp = self.client.get(reverse("transporte:mapa"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Parada ADEFAL Farol")
        self.assertContains(resp, "MCZ-1042")
        self.assertNotContains(resp, "MCZ-9999")

        dados_filtrados = TransporteUrbanoService.obter_dados_mapa_acessivel(
            termo="Farol"
        )
        self.assertEqual(len(dados_filtrados["pontos_mapa"]), 1)
        self.assertEqual(
            dados_filtrados["pontos_mapa"][0]["ponto"].nome,
            "Parada ADEFAL Farol",
        )

