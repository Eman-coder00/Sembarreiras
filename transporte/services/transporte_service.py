import math
from typing import Any
from urllib.parse import urlencode

from django.db.models import Q
from django.urls import reverse

from transporte.exceptions import PontoParadaNaoEncontrado, VeiculoNaoEncontrado
from transporte.models import PontoParada, TipoEquipamentoOnibus, VeiculoAdaptado


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
    def obter_dados_mapa_acessivel(termo: str = "") -> dict[str, Any]:
        filtro = (termo or "").strip()
        pontos_qs = PontoParada.objects.prefetch_related("linhas").all()
        if filtro:
            pontos_qs = pontos_qs.filter(
                Q(nome__icontains=filtro)
                | Q(bairro__icontains=filtro)
                | Q(logradouro__icontains=filtro)
            )
        pontos = list(pontos_qs)

        veiculos_qs = VeiculoAdaptado.objects.select_related("linha").filter(
            acessibilidade_ativa=True,
            linha__ativa=True,
        )
        if filtro:
            veiculos_qs = veiculos_qs.filter(
                Q(linha__itinerario__icontains=filtro)
                | Q(linha__pontos_parada__bairro__icontains=filtro)
                | Q(linha__pontos_parada__nome__icontains=filtro)
            ).distinct()
        veiculos = list(veiculos_qs)

        coords_lat = [float(p.latitude) for p in pontos] + [
            float(v.latitude_atual) for v in veiculos
        ]
        coords_lon = [float(p.longitude) for p in pontos] + [
            float(v.longitude_atual) for v in veiculos
        ]

        if not coords_lat:
            coords_lat = [TransporteUrbanoService.LAT_PADRAO_ADEFAL]
            coords_lon = [TransporteUrbanoService.LON_PADRAO_ADEFAL]

        min_lat, max_lat = min(coords_lat), max(coords_lat)
        min_lon, max_lon = min(coords_lon), max(coords_lon)
        span_lat = max(max_lat - min_lat, 0.008)
        span_lon = max(max_lon - min_lon, 0.008)

        largura, altura, margem = 380.0, 230.0, 36.0

        def _projetar(lat: float, lon: float) -> tuple[int, int]:
            x_norm = (float(lon) - min_lon) / span_lon
            y_norm = (max_lat - float(lat)) / span_lat
            if max_lon == min_lon:
                x_norm = 0.5
            if max_lat == min_lat:
                y_norm = 0.5
            px = int(round(margem + x_norm * (largura - 2 * margem)))
            py = int(round(margem + y_norm * (altura - 2 * margem)))
            return px, py

        pontos_mapa: list[dict[str, Any]] = []
        pontos_json: list[dict[str, Any]] = []
        url_consulta = reverse("transporte:consulta")
        for p in pontos:
            px, py = _projetar(p.latitude, p.longitude)
            linhas_ativas = [ln for ln in p.linhas.all() if ln.ativa]
            eh_adefal = (
                "adefal" in p.nome.lower()
                or "adefal" in p.logradouro.lower()
            )
            query_onibus = urlencode(
                {
                    "origem": p.bairro,
                    "lat": p.latitude,
                    "lon": p.longitude,
                    "raio": 5000,
                }
            )
            pontos_mapa.append(
                {
                    "ponto": p,
                    "linhas": linhas_ativas,
                    "x": px,
                    "y": py,
                    "eh_adefal": eh_adefal,
                }
            )
            pontos_json.append(
                {
                    "id": p.id,
                    "nome": p.nome,
                    "logradouro": p.logradouro,
                    "bairro": p.bairro,
                    "latitude": float(p.latitude),
                    "longitude": float(p.longitude),
                    "eh_adefal": eh_adefal,
                    "linhas": [f"{ln.codigo} - {ln.nome}" for ln in linhas_ativas],
                    "url_onibus": f"{url_consulta}?{query_onibus}",
                }
            )

        veiculos_mapa: list[dict[str, Any]] = []
        veiculos_json: list[dict[str, Any]] = []
        for v in veiculos:
            vx, vy = _projetar(v.latitude_atual, v.longitude_atual)
            veiculos_mapa.append(
                {
                    "veiculo": v,
                    "linha": v.linha,
                    "x": vx,
                    "y": vy,
                }
            )
            veiculos_json.append(
                {
                    "prefixo": v.prefixo,
                    "linha_codigo": v.linha.codigo,
                    "linha_nome": v.linha.nome,
                    "equipamento": TipoEquipamentoOnibus(v.tipo_equipamento).label,
                    "vagas_cadeirante": v.vagas_cadeirante,
                    "latitude": float(v.latitude_atual),
                    "longitude": float(v.longitude_atual),
                    "url_rastrear": reverse(
                        "transporte:rastrear",
                        kwargs={"prefixo": v.prefixo},
                    ),
                }
            )

        return {
            "termo": filtro,
            "pontos_mapa": pontos_mapa,
            "veiculos_mapa": veiculos_mapa,
            "mapa_dados": {
                "centro": [
                    TransporteUrbanoService.LAT_PADRAO_ADEFAL,
                    TransporteUrbanoService.LON_PADRAO_ADEFAL,
                ],
                "pontos": pontos_json,
                "veiculos": veiculos_json,
            },
        }

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

