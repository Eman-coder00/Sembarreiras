import math
from typing import Any

from django.db.models import Q

from transporte.exceptions import PontoParadaNaoEncontrado, VeiculoNaoEncontrado
from transporte.models import PontoParada, VeiculoAdaptado


class TransporteUrbanoService:
    LAT_PADRAO_ADEFAL = -9.64985
    LON_PADRAO_ADEFAL = -35.70895

    @staticmethod
    def calcular_eta_minutos(
        lat_veiculo: float,
        lon_veiculo: float,
        lat_ponto: float,
        lon_ponto: float,
        velocidade_kmh: float = 25.0,
    ) -> tuple[int, int]:
        raio_terra_m = 6371000.0
        phi1 = math.radians(float(lat_veiculo))
        phi2 = math.radians(float(lat_ponto))
        delta_phi = math.radians(float(lat_ponto) - float(lat_veiculo))
        delta_lambda = math.radians(float(lon_ponto) - float(lon_veiculo))

        a = (
            math.sin(delta_phi / 2.0) ** 2
            + math.cos(phi1)
            * math.cos(phi2)
            * (math.sin(delta_lambda / 2.0) ** 2)
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
        distancia_metros = int(round(raio_terra_m * c))

        velocidade_efetiva = max(float(velocidade_kmh), 5.0)
        metros_por_minuto = (velocidade_efetiva * 1000.0) / 60.0
        if distancia_metros <= 0:
            eta_minutos = 1
        else:
            eta_minutos = max(
                1, int(math.ceil(distancia_metros / metros_por_minuto))
            )
        return distancia_metros, eta_minutos

    @staticmethod
    def listar_pontos_parada() -> Any:
        return PontoParada.objects.prefetch_related("linhas").all()

    @staticmethod
    def buscar_veiculos_acessiveis(
        *,
        origem_texto: str = "",
        linha_termo: str = "",
        latitude: float | None = None,
        longitude: float | None = None,
        raio_metros: int = 2000,
    ) -> list[dict[str, Any]]:
        qs = (
            VeiculoAdaptado.objects.select_related("linha")
            .prefetch_related("linha__pontos_parada")
            .filter(
                acessibilidade_ativa=True,
                linha__ativa=True,
            )
        )

        termo = (linha_termo or "").strip()
        if termo:
            qs = qs.filter(
                Q(linha__codigo__icontains=termo)
                | Q(linha__nome__icontains=termo)
                | Q(linha__itinerario__icontains=termo)
            )

        origem = (origem_texto or "").strip()
        ponto_referencia = None
        if origem:
            ponto_referencia = PontoParada.objects.filter(
                Q(nome__icontains=origem)
                | Q(bairro__icontains=origem)
                | Q(logradouro__icontains=origem)
            ).first()
            qs = qs.filter(
                Q(linha__itinerario__icontains=origem)
                | Q(linha__pontos_parada__bairro__icontains=origem)
                | Q(linha__pontos_parada__nome__icontains=origem)
                | Q(linha__pontos_parada__logradouro__icontains=origem)
            ).distinct()

        if latitude is not None and longitude is not None:
            lat_ref = float(latitude)
            lon_ref = float(longitude)
        elif ponto_referencia is not None:
            lat_ref = float(ponto_referencia.latitude)
            lon_ref = float(ponto_referencia.longitude)
        else:
            lat_ref = TransporteUrbanoService.LAT_PADRAO_ADEFAL
            lon_ref = TransporteUrbanoService.LON_PADRAO_ADEFAL

        limite_raio = max(int(raio_metros or 2000), 100)
        resultados: list[dict[str, Any]] = []

        for veiculo in qs:
            distancia_m, eta_min = TransporteUrbanoService.calcular_eta_minutos(
                lat_veiculo=veiculo.latitude_atual,
                lon_veiculo=veiculo.longitude_atual,
                lat_ponto=lat_ref,
                lon_ponto=lon_ref,
                velocidade_kmh=veiculo.velocidade_media_kmh,
            )
            if distancia_m <= limite_raio:
                ponto_proximo = veiculo.linha.pontos_parada.first()
                resultados.append(
                    {
                        "veiculo": veiculo,
                        "linha": veiculo.linha,
                        "ponto_parada": ponto_referencia or ponto_proximo,
                        "distancia_metros": distancia_m,
                        "eta_minutos": eta_min,
                        "mensagem_eta": (
                            f"Próximo ônibus adaptado chega em aproximadamente {eta_min} minutos"
                        ),
                    }
                )

        resultados.sort(key=lambda item: (item["eta_minutos"], item["distancia_metros"]))
        return resultados

    @staticmethod
    def rastrear_veiculo(
        prefixo: str,
        ponto_id: int | None = None,
    ) -> dict[str, Any]:
        try:
            veiculo = (
                VeiculoAdaptado.objects.select_related("linha")
                .prefetch_related("linha__pontos_parada")
                .get(
                    prefixo__iexact=(prefixo or "").strip(),
                    acessibilidade_ativa=True,
                    linha__ativa=True,
                )
            )
        except VeiculoAdaptado.DoesNotExist as exc:
            raise VeiculoNaoEncontrado(
                "Ônibus adaptado não encontrado ou sem acessibilidade física ativa."
            ) from exc

        if ponto_id is not None:
            try:
                ponto = PontoParada.objects.get(pk=ponto_id)
            except PontoParada.DoesNotExist as exc:
                raise PontoParadaNaoEncontrado(
                    "Ponto de parada informado não existe."
                ) from exc
        else:
            ponto = veiculo.linha.pontos_parada.first()

        lat_ponto = (
            float(ponto.latitude)
            if ponto is not None
            else TransporteUrbanoService.LAT_PADRAO_ADEFAL
        )
        lon_ponto = (
            float(ponto.longitude)
            if ponto is not None
            else TransporteUrbanoService.LON_PADRAO_ADEFAL
        )

        distancia_m, eta_min = TransporteUrbanoService.calcular_eta_minutos(
            lat_veiculo=veiculo.latitude_atual,
            lon_veiculo=veiculo.longitude_atual,
            lat_ponto=lat_ponto,
            lon_ponto=lon_ponto,
            velocidade_kmh=veiculo.velocidade_media_kmh,
        )

        return {
            "veiculo": veiculo,
            "linha": veiculo.linha,
            "ponto": ponto,
            "distancia_metros": distancia_m,
            "eta_minutos": eta_min,
            "mensagem_eta": (
                f"Próximo ônibus adaptado chega em aproximadamente {eta_min} minutos"
            ),
        }

