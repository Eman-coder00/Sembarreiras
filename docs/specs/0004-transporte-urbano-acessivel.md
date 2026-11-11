# Spec 0004: Transporte urbano acessível

- **Status:** Implementado
- **Requisitos:** RF-12 a RF-14 e RNF-05 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)
- **Depende de:** [Spec 0002](0002-contas-vinculo-e-acessibilidade.md)

## Modelos (`transporte/models/`)

### `LinhaOnibus`

| Campo | Tipo | Regras |
|---|---|---|
| `codigo` | `CharField(max_length=20, unique=True)` | Obrigatório (ex.: `"051"`, `"704"`) |
| `nome` | `CharField(max_length=100)` | Obrigatório (ex.: `"Santos Dumont / Trapiche"`) |
| `itinerario` | `TextField` | Bairros e vias atendidos (incluindo referência à ADEFAL / Farol) |
| `ativa` | `BooleanField(default=True)` | |

### `PontoParada`

| Campo | Tipo | Regras |
|---|---|---|
| `nome` | `CharField(max_length=100)` | Obrigatório |
| `logradouro` | `CharField(max_length=120)` | Obrigatório |
| `bairro` | `CharField(max_length=80)` | Obrigatório |
| `latitude` | `FloatField` | Obrigatório |
| `longitude` | `FloatField` | Obrigatório |
| `linhas` | `ManyToManyField(LinhaOnibus, related_name="pontos_parada")` | |

### `VeiculoAdaptado`

| Campo | Tipo | Regras |
|---|---|---|
| `prefixo` | `CharField(max_length=20, unique=True)` | Obrigatório (ex.: `"MCZ-1042"`) |
| `linha` | `ForeignKey(LinhaOnibus, on_delete=PROTECT, related_name="veiculos")` | Obrigatório |
| `acessibilidade_ativa` | `BooleanField(default=True)` | Indica se o elevador ou rampa está funcional na telemetria |
| `tipo_equipamento` | `CharField` com `TextChoices` | `ELEVADOR_HIDRAULICO`, `RAMPA_ACESSIVEL` |
| `vagas_cadeirante` | `PositiveSmallIntegerField(default=1)` | |
| `latitude_atual` | `FloatField` | Posição geográfica atual |
| `longitude_atual` | `FloatField` | Posição geográfica atual |
| `velocidade_media_kmh` | `FloatField(default=25.0)` | Velocidade média do tráfego na via |
| `atualizado_em` | `DateTimeField(auto_now=True)` | |

## Exceções (`transporte/exceptions.py`)

- `VeiculoNaoEncontrado`: veículo não existe ou não está com acessibilidade física ativa.
- `PontoParadaNaoEncontrado`: ponto de parada informado não existe.

## `TransporteUrbanoService` (`transporte/services/`)

| Método | Regra |
|---|---|
| `buscar_veiculos_acessiveis(origem_texto="", linha_termo="", latitude=None, longitude=None, raio_metros=2000)` | Filtra obrigatoriamente `acessibilidade_ativa=True` e `linha__ativa=True`. Aplica filtro opcional por código/nome/itinerário da linha e proximidade do ponto de parada dentro de `raio_metros`. Retorna lista ordenada pelo menor tempo estimado de chegada (ETA) |
| `obter_dados_mapa_acessivel(termo="")` | Lista pontos de parada (`PontoParada`) e veículos com acessibilidade ativa (`acessibilidade_ativa=True`, `linha__ativa=True`), aplicando filtro opcional por bairro/ponto e projetando coordenadas normalizadas `(x, y)` para o mapa local em SVG |
| `rastrear_veiculo(prefixo, ponto_id=None)` | Retorna os dados do veículo adaptado (`acessibilidade_ativa=True`, ou levanta `VeiculoNaoEncontrado`), distância em metros até o ponto de parada e o ETA calculado |
| `calcular_eta_minutos(lat_veiculo, lon_veiculo, lat_ponto, lon_ponto, velocidade_kmh)` | Calcula a distância geodésica aproximada (fórmula de Haversine) em metros e retorna `(distancia_metros, eta_minutos)` com mínimo de 1 minuto quando em deslocamento |

## Rotas (`app_name = "transporte"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/transporte/` | `transporte:consulta` | `LinhaAcessivelConsultaView` | GET | Autenticado |
| `/transporte/mapa/` | `transporte:mapa` | `MapaAcessivelView` | GET | Autenticado |
| `/transporte/veiculos/<str:prefixo>/` | `transporte:rastrear` | `VeiculoRastreamentoView` | GET | Autenticado |

## Comportamento

- **`LinhaAcessivelConsultaView`**: recebe filtros via query string (`origem`, `linha`, `raio`, `lat`, `lon`), chama `TransporteUrbanoService.buscar_veiculos_acessiveis` e exibe apenas veículos com elevador ou rampa funcional comprovada, ordenados pelo tempo estimado de chegada.
- **`MapaAcessivelView`**: renderiza o mapa interativo com **Leaflet + OpenStreetMap** (sem chave de API) e fallback automático para mapa local em SVG quando offline ([ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)), plotando pontos de parada (`PontoParada`), a Sede da ADEFAL e ônibus acessíveis ativos, com filtro por bairro/parada, geolocalização opcional e atalhos para listar veículos próximos de cada ponto.
- **`VeiculoRastreamentoView`**: exibe a posição atual do ônibus adaptado selecionado, a distância em metros até o ponto de parada e o indicador destacado `"Próximo ônibus adaptado chega em aproximadamente X minutos"`, sem vincular a identidade pessoal do usuário na consulta de trânsito (`RS009`).

## Testes

- [x] A busca retorna exclusivamente veículos com `acessibilidade_ativa=True`; ônibus com elevador inoperante (`acessibilidade_ativa=False`) nunca aparecem na listagem.
- [x] O filtro por número da linha ou destino/bairro retorna apenas os veículos correspondentes dentro do raio informado.
- [x] `calcular_eta_minutos` retorna a distância em metros e o tempo estimado em minutos de forma consistente com a velocidade média.
- [x] `rastrear_veiculo` exibe a distância e a mensagem `"Próximo ônibus adaptado chega em aproximadamente X minutos"` para veículo acessível, e retorna 404 para prefixo inexistente ou sem acessibilidade ativa.
- [x] `MapaAcessivelView` e `obter_dados_mapa_acessivel` exibem pontos de parada acessíveis e apenas veículos com `acessibilidade_ativa=True`, permitindo filtragem por bairro/ponto.

