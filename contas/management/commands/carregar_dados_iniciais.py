from django.core.management.base import BaseCommand

from contas.services import DadosIniciaisService


class Command(BaseCommand):
    help = "Popula dados iniciais idempotentes de Maceió/AL e da ADEFAL (CEPs, ônibus, agenda e frota)."

    def handle(self, *args, **options):
        resumo = DadosIniciaisService.carregar_tudo()
        self.stdout.write(
            self.style.SUCCESS(
                f"Dados iniciais carregados com sucesso: "
                f"{resumo['ceps']} CEPs, {resumo['linhas']} linhas, "
                f"{resumo['veiculos']} veículos, {resumo['vagas_adefal']} vagas ADEFAL, "
                f"{resumo['frota_adaptada']} rotas de frota adaptada."
            )
        )

