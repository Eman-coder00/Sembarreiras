import importlib
import inspect
import pkgutil

from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver
from django.views import View

import agendamentos.views
import contas.views
import core.urls
import emergencia.views
import equipamentos.views
import transporte.views

PACOTES_DE_VIEWS = (
    contas.views,
    emergencia.views,
    transporte.views,
    agendamentos.views,
    equipamentos.views,
)


def _modulos_de_views():
    for pacote in PACOTES_DE_VIEWS:
        yield pacote
        for info in pkgutil.iter_modules(pacote.__path__):
            yield importlib.import_module(f"{pacote.__name__}.{info.name}")


def _padroes_de_url(padroes):
    for padrao in padroes:
        if isinstance(padrao, URLPattern):
            yield padrao
        elif isinstance(padrao, URLResolver) and padrao.app_name != "admin":
            yield from _padroes_de_url(padrao.url_patterns)


class ArquiteturaTests(SimpleTestCase):
    def test_classes_de_view_herdam_diretamente_de_view(self):
        classes = [
            classe
            for modulo in _modulos_de_views()
            for nome, classe in inspect.getmembers(modulo, inspect.isclass)
            if classe.__module__ == modulo.__name__ and nome.endswith("View")
        ]

        self.assertTrue(classes, "Nenhuma classe de view foi encontrada.")
        for classe in classes:
            with self.subTest(view=f"{classe.__module__}.{classe.__name__}"):
                self.assertIn(View, classe.__bases__)

    def test_rotas_apontam_para_views_criadas_com_as_view(self):
        padroes = list(_padroes_de_url(core.urls.urlpatterns))

        self.assertTrue(padroes, "Nenhuma rota foi encontrada.")
        for padrao in padroes:
            with self.subTest(rota=padrao.name):
                self.assertTrue(hasattr(padrao.callback, "view_class"))

