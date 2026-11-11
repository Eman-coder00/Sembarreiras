# Spec 0007: Dados iniciais de demonstração

- **Status:** Implementado
- **Decisões:** [ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)
- **Depende de:** [Spec 0002](0002-contas-vinculo-e-acessibilidade.md), [Spec 0004](0004-transporte-urbano-acessivel.md), [Spec 0005](0005-agendamentos-e-transporte-hospitalar.md)

O comando abaixo popula o banco com dados iniciais realistas de Maceió/AL e da ADEFAL para que o sistema possa ser demonstrado e avaliado imediatamente após o `migrate`:

```bash
python manage.py carregar_dados_iniciais
```

- A gravação é feita por `DadosIniciaisService.carregar_tudo()`, que cria de forma idempotente:
  1. **CEPs locais (`CepLocal`)**: faixas de CEP de bairros de Maceió (Farol, Trapiche da Barra, Pajuçara, Ponta Verde, Benedito Bentes, Jatiúca) incluindo o endereço da Sede da ADEFAL.
  2. **Linhas, pontos de parada e ônibus (`LinhaOnibus`, `PontoParada`, `VeiculoAdaptado`)**: linhas municipais de Maceió com veículos adaptados (`acessibilidade_ativa=True`) e veículos sem acessibilidade (`acessibilidade_ativa=False`, para demonstrar a filtragem obrigatória).
  3. **Agenda e frota da ADEFAL (`VagaAgendaADEFAL`, `VagaFrotaAdaptada`)**: horários disponíveis nas especialidades (Fisioterapia, Ortopedia, Terapia Ocupacional, Neurologia e Consulta Geral) com datas futuras para testar agendamentos imediato, >24h e >48h, além de vans adaptadas com vagas de cadeirante.
- O comando pode ser executado repetidas vezes sem duplicar registros (`get_or_create` / `update_or_create`).
- Não se usa migração de dados, para que os dados iniciais não interfiram nos testes unitários isolados.

## Testes

- [x] Executar `carregar_dados_iniciais` duas vezes seguidas popula CEPs, linhas de ônibus, vagas da ADEFAL e frota adaptada sem duplicar registros.

