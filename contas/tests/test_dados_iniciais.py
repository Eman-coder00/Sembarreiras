from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from agendamentos.models import VagaAgendaADEFAL, VagaFrotaAdaptada
from contas.models import CepLocal
from transporte.models import LinhaOnibus, VeiculoAdaptado


class CarregarDadosIniciaisCommandTest(TestCase):
    def test_carregar_dados_iniciais_eh_idempotente(self):
        out1 = StringIO()
        call_command("carregar_dados_iniciais", stdout=out1)
        self.assertIn("Dados iniciais carregados com sucesso", out1.getvalue())

        qtd_ceps = CepLocal.objects.count()
        qtd_linhas = LinhaOnibus.objects.count()
        qtd_veiculos = VeiculoAdaptado.objects.count()
        qtd_vagas = VagaAgendaADEFAL.objects.count()
        qtd_frota = VagaFrotaAdaptada.objects.count()

        self.assertGreaterEqual(qtd_ceps, 6)
        self.assertGreaterEqual(qtd_linhas, 3)
        self.assertGreaterEqual(qtd_veiculos, 4)
        self.assertGreaterEqual(qtd_vagas, 20)
        self.assertGreaterEqual(qtd_frota, 4)

        # Executa uma segunda vez e garante que não duplica registros
        out2 = StringIO()
        call_command("carregar_dados_iniciais", stdout=out2)
        self.assertEqual(CepLocal.objects.count(), qtd_ceps)
        self.assertEqual(LinhaOnibus.objects.count(), qtd_linhas)
        self.assertEqual(VeiculoAdaptado.objects.count(), qtd_veiculos)
        self.assertEqual(VagaAgendaADEFAL.objects.count(), qtd_vagas)
        self.assertEqual(VagaFrotaAdaptada.objects.count(), qtd_frota)

