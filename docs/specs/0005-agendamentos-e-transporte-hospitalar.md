# Spec 0005: Agendamentos na ADEFAL e transporte hospitalar adaptado

- **Status:** Implementado
- **Requisitos:** RF-15 a RF-18, RNF-03 e RNF-05 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0003](../adr/0003-postgresql-como-banco-de-dados.md), [ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)
- **Depende de:** [Spec 0002](0002-contas-vinculo-e-acessibilidade.md)

## Modelos (`agendamentos/models/`)

### `VagaAgendaADEFAL`

| Campo | Tipo | Regras |
|---|---|---|
| `especialidade` | `CharField` com `TextChoices` | `FISIOTERAPIA`, `ORTOPEDIA`, `TERAPIA_OCUPACIONAL`, `NEUROLOGIA`, `CONSULTA_GERAL` |
| `unidade` | `CharField` com `TextChoices` | `SEDE_MACEIO`, `UNIDADE_REGIONAL` |
| `profissional` | `CharField(max_length=100)` | Obrigatório |
| `data` | `DateField` | Obrigatório |
| `horario` | `TimeField` | Obrigatório |
| `disponivel` | `BooleanField(default=True)` | |

No `Meta`: `UniqueConstraint` em `(unidade, profissional, data, horario)`.

### `Consulta`

| Campo | Tipo | Regras |
|---|---|---|
| `protocolo` | `CharField(max_length=24, unique=True)` | Formato `CNS-AAAAMMDD-XXXX`, gerado pelo service |
| `paciente_pcd` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="consultas")` | Obrigatório |
| `solicitado_por` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="consultas_solicitadas")` | Titular PCD ou Cuidador vinculado |
| `vaga` | `ForeignKey(VagaAgendaADEFAL, on_delete=PROTECT, related_name="agendamentos")` | Obrigatório |
| `status` | `IntegerField` com `IntegerChoices` | `CONFIRMADO = 1`, `REALIZADO = 2`, `CANCELADO = 3`, `REAGENDADO = 4` |
| `justificativa_alteracao` | `CharField(max_length=200, blank=True)` | |
| `assinatura_qr` | `CharField(max_length=64)` | Hash HMAC-SHA256 gerado pelo service |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |
| `atualizado_em` | `DateTimeField(auto_now=True)` | |

### `VagaFrotaAdaptada`

| Campo | Tipo | Regras |
|---|---|---|
| `data` | `DateField` | Obrigatório |
| `turno_horario` | `TimeField` | Horário de referência |
| `veiculo_identificacao` | `CharField(max_length=60)` | Ex.: `"Van Adaptada ADEFAL 01"` |
| `motorista` | `CharField(max_length=80)` | |
| `vagas_cadeirante_total` | `PositiveSmallIntegerField(default=4)` | |
| `vagas_cadeirante_ocupadas` | `PositiveSmallIntegerField(default=0)` | |

### `SolicitacaoTransporte`

| Campo | Tipo | Regras |
|---|---|---|
| `consulta` | `OneToOneField(Consulta, on_delete=PROTECT, related_name="transporte")` | Obrigatório |
| `frota` | `ForeignKey(VagaFrotaAdaptada, on_delete=PROTECT, related_name="reservas")` | Obrigatório |
| `endereco_embarque` | `CharField(max_length=250)` | Herdado do cadastro do titular com opção de edição pontual |
| `precisa_acompanhante` | `BooleanField(default=False)` | Obrigatório |
| `equipamento_transporte` | `CharField` com `TextChoices` | `CADEIRA_MANUAL`, `CADEIRA_MOTORIZADA`, `MACA`, `MULETAS` |
| `horario_apanhe_previsto` | `TimeField` | Calculado pelo service (1 hora antes da consulta) |
| `status` | `IntegerField` com `IntegerChoices` | `SOLICITADO = 1`, `ROTA_CONFIRMADA = 2`, `A_CAMINHO = 3`, `CONCLUIDO = 4`, `CANCELADO = 5` |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

## Exceções (`agendamentos/exceptions.py`)

- `VagaIndisponivel`: vaga já ocupada ou conflito de horário para o mesmo paciente.
- `AgendamentoNaoEncontrado`: protocolo inexistente ou solicitante sem permissão sobre o paciente.
- `PrazoMinimo24hConsulta`: tentativa de cancelar ou remarcar consulta faltando menos de 24 horas para o atendimento.
- `PrazoMinimo48hTransporte`: tentativa de solicitar transporte hospitalar faltando menos de 48 horas para a consulta.
- `SemVagaFrotaAdaptada`: frota adaptada sem saldo de vagas de cadeirante para a data/horário.
- `ComprovanteInvalido`: assinatura HMAC do QR Code inválida ou adulterada.

## Services (`agendamentos/services/`)

### `AgendamentoService`

| Método | Regra |
|---|---|
| `listar_vagas_disponiveis(especialidade=None, unidade=None, data=None)` | Retorna vagas futuras com `disponivel=True` |
| `agendar(solicitante, vaga_id, titular_cpf=None)` | Verifica permissão (`ContaService.obter_titular_autorizado`), bloqueia a vaga com `select_for_update()` dentro de `transaction.atomic()`, impede conflito de horário do paciente, gera protocolo `CNS-AAAAMMDD-XXXX` e assinatura HMAC-SHA256 |
| `cancelar(solicitante, protocolo, justificativa="")` | Exige antecedência mínima de 24 horas (`PrazoMinimo24hConsulta`). Libera a vaga da ADEFAL e, se houver `SolicitacaoTransporte` ativa, cancela-a automaticamente devolvendo a vaga na van |
| `remarcar(solicitante, protocolo, nova_vaga_id, justificativa="")` | Exige antecedência mínima de 24 horas, libera a vaga antiga, marca a consulta anterior como `REAGENDADO` e cria o novo agendamento ajustando ou liberando o transporte associado |

### `TransporteHospitalarService`

| Método | Regra |
|---|---|
| `solicitar_transporte(solicitante, protocolo_consulta, endereco_embarque, precisa_acompanhante, equipamento_transporte)` | Exige consulta `CONFIRMADO` com antecedência mínima de 48 horas (`PrazoMinimo48hTransporte`) e saldo de vagas em `VagaFrotaAdaptada` (`SemVagaFrotaAdaptada`). Reserva a vaga em `transaction.atomic()` |
| `cancelar_transporte(solicitante, protocolo_consulta)` | Exige antecedência mínima de 24 horas antes do trajeto, altera status para `CANCELADO` e libera a vaga na van |

### `ComprovanteService`

| Método | Regra |
|---|---|
| `gerar_assinatura(protocolo, cpf, data_iso, horario_iso)` | Retorna `hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()` |
| `validar_comprovante(protocolo, assinatura)` | Verifica com `hmac.compare_digest` se a assinatura confere com a consulta ativa, levantando `ComprovanteInvalido` em caso de fraude ou adulteração (`RS006`) |

## Rotas (`app_name = "agendamentos"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/agendamentos/` | `agendamentos:lista` | `ConsultaListView` | GET | Titular PCD ou Cuidador vinculado |
| `/agendamentos/novo/` | `agendamentos:criar` | `ConsultaCreateView` | GET, POST | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/` | `agendamentos:detalhe` | `ConsultaDetailView` | GET | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/cancelar/` | `agendamentos:cancelar` | `ConsultaCancelarView` | POST | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/remarcar/` | `agendamentos:remarcar` | `ConsultaRemarcarView` | GET, POST | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/transporte/` | `agendamentos:solicitar_transporte` | `TransporteSolicitarView` | GET, POST | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/transporte/cancelar/` | `agendamentos:cancelar_transporte` | `TransporteCancelarView` | POST | Titular PCD ou Cuidador vinculado |
| `/agendamentos/<str:protocolo>/comprovante/` | `agendamentos:comprovante` | `ComprovanteDigitalView` | GET | Titular PCD, Cuidador vinculado ou Staff |
| `/agendamentos/portaria/validar/` | `agendamentos:validar_qr` | `PortariaValidarQRView` | GET, POST | Staff / Recepção ADEFAL |

## Testes

- [x] Agendamento em vaga disponível gera protocolo `CNS-AAAAMMDD-XXXX`, marca a vaga como indisponível e impede duplo agendamento na mesma vaga.
- [x] Cancelar ou remarcar consulta com mais de 24h de antecedência libera a vaga e cancela automaticamente o transporte hospitalar vinculado.
- [x] Tentar cancelar ou remarcar consulta faltando menos de 24h é bloqueado com `PrazoMinimo24hConsulta`.
- [x] Solicitar transporte hospitalar com pelo menos 48h de antecedência e vaga na van confirma a reserva e reduz o saldo disponível.
- [x] Solicitar transporte faltando menos de 48h (`PrazoMinimo48hTransporte`) ou sem vaga na frota (`SemVagaFrotaAdaptada`) é rejeitado.
- [x] Comprovante digital exibe QR Code assinado, e `PortariaValidarQRView` aceita assinatura autêntica e rejeita assinatura adulterada (`ComprovanteInvalido`).
- [x] Cuidador com vínculo `APROVADO` agenda e visualiza consultas do titular; usuário sem vínculo recebe 404/403.

