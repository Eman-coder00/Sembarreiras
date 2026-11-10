# Spec 0003: Emergência e botão de pânico

- **Status:** Proposto
- **Requisitos:** RF-07 a RF-11, RNF-02 e RNF-05 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)
- **Depende de:** [Spec 0002](0002-contas-vinculo-e-acessibilidade.md)

## Modelos (`emergencia/models/`)

### `ContatoEmergencia`

| Campo | Tipo | Regras |
|---|---|---|
| `titular_pcd` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="contatos_emergencia")` | Obrigatório |
| `nome` | `CharField(max_length=100)` | Obrigatório, mínimo de 3 caracteres |
| `telefone` | `CharField(max_length=15)` | Obrigatório, formato `(XX) 9XXXX-XXXX` com DDD válido |
| `parentesco` | `CharField` com `TextChoices` | `FAMILIAR`, `AMIGO`, `CUIDADOR`, `VIZINHO`, `OUTRO` |
| `prioridade` | `PositiveSmallIntegerField` | `1` (1ª Prioridade), `2` (2ª Prioridade) ou `3` (3ª Prioridade) |
| `status` | `IntegerField` com `IntegerChoices` | `ATIVO = 1`, `INATIVO = 2` (padrão `ATIVO`) |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

No `Meta`:
- `CheckConstraint`: `prioridade` entre 1 e 3.
- `UniqueConstraint` parcial em `(titular_pcd, prioridade)` quando `status = ATIVO`.
- Ordenação padrão por `prioridade`.

### `OcorrenciaPanico`

| Campo | Tipo | Regras |
|---|---|---|
| `codigo` | `CharField(max_length=24, unique=True)` | Gerado automaticamente (ex.: `PAN-AAAAMMDD-XXXX`) |
| `titular_pcd` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="ocorrencias_panico")` | Obrigatório |
| `latitude` | `FloatField(null=True, blank=True)` | Preenchido no disparo |
| `longitude` | `FloatField(null=True, blank=True)` | Preenchido no disparo |
| `endereco_aproximado` | `CharField(max_length=200, blank=True)` | Gerado por geocodificação reversa local |
| `status` | `CharField` com `TextChoices` | `EM_CONTAGEM`, `CANCELADO`, `ENTREGUE`, `FALHA_PARCIAL`, `FALLBACK_SMS` |
| `contatos_notificados` | `TextField(blank=True)` | Relação dos nomes e telefones acionados |
| `criado_em` | `DateTimeField(auto_now_add=True)` | Timestamp de início |
| `finalizado_em` | `DateTimeField(null=True, blank=True)` | Timestamp de disparo ou cancelamento |

## Exceções (`emergencia/exceptions.py`)

- `LimiteContatosExcedido`: o titular já possui 3 contatos de emergência ativos ou a prioridade escolhida já está ocupada.
- `MinimoContatoAtivoObrigatorio`: tentativa de excluir ou inativar o único contato de emergência ativo da conta.
- `SemContatosDeEmergencia`: tentativa de acionar o botão de pânico sem nenhum contato ativo cadastrado.
- `OcorrenciaNaoEncontrada`: ocorrência não existe ou pertence a outro titular sem vínculo autorizado.
- `JanelaCancelamentoEncerrada`: tentativa de cancelar um alerta que já foi disparado.

## Services (`emergencia/services/`)

### `ContatoEmergenciaService`

| Método | Regra |
|---|---|
| `listar_ativos(titular_pcd)` | Retorna contatos ativos ordenados por `prioridade` (1º, 2º, 3º) |
| `criar(titular_pcd, nome, telefone, parentesco, prioridade)` | Verifica limite de 3 contatos ativos e disponibilidade da prioridade antes de gravar |
| `atualizar(contato_id, titular_pcd, ...)` | Atualiza dados do contato garantindo que ao menos 1 contato continue ativo |
| `excluir(contato_id, titular_pcd)` | Impede a exclusão caso seja o único contato ativo (`MinimoContatoAtivoObrigatorio`) |

### `PanicoService`

| Método | Regra |
|---|---|
| `iniciar_acionamento(titular_pcd, latitude=None, longitude=None)` | Exige ao menos 1 contato ativo (`SemContatosDeEmergencia`). Cria `OcorrenciaPanico(status="EM_CONTAGEM")` |
| `cancelar_alerta(ocorrencia_id, titular_pcd)` | Se `status == "EM_CONTAGEM"`, muda para `CANCELADO`, preenche `finalizado_em` e não envia nenhuma mensagem externa |
| `confirmar_disparo(ocorrencia_id, titular_pcd, latitude, longitude, falha_dados=False)` | Captura as coordenadas, monta a mensagem `"EMERGÊNCIA! Preciso de ajuda imediata. Minha localização atual é: ..."` e aciona os contatos ativos por ordem de prioridade. Se `falha_dados=True`, aciona fallback automático via SMS nativo (`status="FALLBACK_SMS"`), senão grava `status="ENTREGUE"` |
| `listar_historico(solicitante, titular_cpf=None, data_inicio=None, data_fim=None, status=None)` | Verifica permissão (titular PCD ou cuidador com vínculo `APROVADO`) e retorna as ocorrências filtradas das mais recentes para as mais antigas |

## Rotas (`app_name = "emergencia"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/emergencia/contatos/` | `emergencia:contatos` | `ContatoEmergenciaListView` | GET, POST | Autenticado (PCD) |
| `/emergencia/contatos/<int:contato_id>/editar/` | `emergencia:editar_contato` | `ContatoEmergenciaUpdateView` | GET, POST | Dono (PCD) |
| `/emergencia/contatos/<int:contato_id>/excluir/` | `emergencia:excluir_contato` | `ContatoEmergenciaDeleteView` | POST | Dono (PCD) |
| `/emergencia/panico/` | `emergencia:panico` | `BotaoPanicoView` | GET, POST | Autenticado (PCD) |
| `/emergencia/panico/<int:ocorrencia_id>/contagem/` | `emergencia:contagem` | `ContagemRegressivaView` | GET | Dono (PCD) |
| `/emergencia/panico/<int:ocorrencia_id>/cancelar/` | `emergencia:cancelar` | `CancelarPanicoView` | POST | Dono (PCD) |
| `/emergencia/panico/<int:ocorrencia_id>/disparar/` | `emergencia:disparar` | `DispararPanicoView` | POST | Dono (PCD) |
| `/emergencia/historico/` | `emergencia:historico` | `HistoricoPanicoView` | GET | Titular PCD ou Cuidador vinculado |

## Comportamento

1. Na tela do Botão de Pânico (`BotaoPanicoView`), os contatos ativos ficam sincronizados em `localStorage` no navegador para resiliência offline.
2. Ao acionar o botão, `PanicoService.iniciar_acionamento` cria o registro em contagem e redireciona para `ContagemRegressivaView`, que exibe a janela de 5 segundos com botão destacado "Cancelar Alerta".
3. Se o usuário tocar em "Cancelar Alerta" (`CancelarPanicoView`), o disparo externo é abortado e a mensagem `"Alerta cancelado com sucesso"` é exibida.
4. Ao concluir a contagem (`DispararPanicoView`), o alerta é enviado com as coordenadas de GPS aos contatos prioritários (com fallback automático para SMS se não houver dados móveis) e registrado de forma imutável no histórico.

## Admin

`OcorrenciaPanico` é somente leitura no Admin (`has_add_permission`, `has_change_permission` e `has_delete_permission` retornam `False`), garantindo a imutabilidade do registro de auditoria.

## Testes

- [ ] Usuário PCD cadastra até 3 contatos prioritários; tentar cadastrar o 4º contato ativo levanta `LimiteContatosExcedido`.
- [ ] Tentar excluir o único contato de emergência ativo é bloqueado com `MinimoContatoAtivoObrigatorio`.
- [ ] Acionar pânico sem contatos ativos é rejeitado com mensagem orientando o cadastro de contato.
- [ ] Cancelar o alerta durante a contagem regressiva grava `CANCELADO`, exibe `"Alerta cancelado com sucesso"` e não envia mensagens externas.
- [ ] Confirmar o disparo grava coordenadas, lista de contatos notificados e texto padrão com link de localização.
- [ ] Em caso de falha no canal de dados (`falha_dados=True`), o service realiza fallback automático para SMS (`FALLBACK_SMS`).
- [ ] Cuidador com vínculo `APROVADO` visualiza o histórico de ocorrências do titular, mas cuidador sem vínculo ativo ou outro usuário recebe 404/403.

