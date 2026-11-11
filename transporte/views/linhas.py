from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import render
from django.views import View

from transporte.exceptions import PontoParadaNaoEncontrado, VeiculoNaoEncontrado
from transporte.forms import (
    FiltroLinhasAcessiveisForm,
    FiltroMapaAcessivelForm,
)
from transporte.services import TransporteUrbanoService


class LinhaAcessivelConsultaView(LoginRequiredMixin, View):
    def get(self, request):
        form = FiltroLinhasAcessiveisForm(request.GET or None)
        origem = ""
        linha = ""
        raio = 5000
        lat = None
        lon = None

        if form.is_valid():
            origem = form.cleaned_data.get("origem") or ""
            linha = form.cleaned_data.get("linha") or ""
            raio = form.cleaned_data.get("raio") or 5000
            lat = form.cleaned_data.get("lat")
            lon = form.cleaned_data.get("lon")

        resultados = TransporteUrbanoService.buscar_veiculos_acessiveis(
            origem_texto=origem,
            linha_termo=linha,
            latitude=lat,
            longitude=lon,
            raio_metros=raio,
        )
        pontos = TransporteUrbanoService.listar_pontos_parada()

        return render(
            request,
            "transporte/consulta.html",
            {
                "form": form,
                "resultados": resultados,
                "pontos": pontos,
            },
        )


class MapaAcessivelView(LoginRequiredMixin, View):
    def get(self, request):
        form = FiltroMapaAcessivelForm(request.GET or None)
        busca = ""
        if form.is_valid():
            busca = form.cleaned_data.get("busca") or ""

        dados = TransporteUrbanoService.obter_dados_mapa_acessivel(termo=busca)
        return render(
            request,
            "transporte/mapa.html",
            {
                "form": form,
                **dados,
            },
        )


class VeiculoRastreamentoView(LoginRequiredMixin, View):
    def get(self, request, prefixo: str):
        ponto_id_str = request.GET.get("ponto_id", "").strip()
        ponto_id = int(ponto_id_str) if ponto_id_str.isdigit() else None

        try:
            dados = TransporteUrbanoService.rastrear_veiculo(
                prefixo=prefixo,
                ponto_id=ponto_id,
            )
        except (VeiculoNaoEncontrado, PontoParadaNaoEncontrado) as exc:
            raise Http404 from exc

        return render(
            request,
            "transporte/rastrear.html",
            dados,
        )
