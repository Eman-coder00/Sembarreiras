# Spec 0006: Empréstimo de equipamentos de apoio e validação de laudos

- **Status:** Proposto
- **Requisitos:** RF-19 a RF-22, RNF-03 e RNF-04 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0003](../adr/0003-postgresql-como-banco-de-dados.md), [ADR 0005](../adr/0005-armazenamento-e-validacao-de-anexos.md)
- **Depende de:** [Spec 0002](0002-contas-vinculo-e-acessibilidade.md)

## Modelos (`equipamentos/models/`)

### `SolicitacaoEquipamento`

| Campo | Tipo | Regras |
|---|---|---|
| `protocolo` | `CharField(max_length=24, unique=True)` | Formato `EQP-AAAAMMDD-XXXX`, gerado pelo service |
| `beneficiario_pcd` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="solicitacoes_equipamento")` | Obrigatório |
| `solicitado_por` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="equipamentos_requisitados")` | Titular PCD ou Cuidador vinculado |
| `tipo_equipamento` | `CharField` com `TextChoices` | `CADEIRA_MANUAL`, `CADEIRA_MOTORIZADA`, `CADEIRA_BANHO`, `MULETA_BENGALA`, `ANDADOR`, `ORTESE_PROTESE` |
| `largura_quadril_cm` | `PositiveSmallIntegerField` | Obrigatório |
| `altura_cm` | `PositiveSmallIntegerField` | Obrigatório |
| `peso_kg` | `DecimalField(max_digits=5, decimal_places=2)` | Obrigatório |
| `observacoes_clinicas` | `TextField(max_length=500, blank=True)` | Opcional |
| `crm_medico` | `CharField(max_length=30, blank=True)` | Opcional |
| `data_emissao_laudo` | `DateField(null=True, blank=True)` | Opcional |
| `arquivo_laudo` | `FileField(upload_to=...)` | Caminho com `uuid4`, PDF/JPG/PNG até 10 MB |
| `arquivo_comprovante_residencia` | `FileField(upload_to=...)` | Caminho com `uuid4`, PDF/JPG/PNG até 5 MB |
| `status` | `IntegerField` com `IntegerChoices` | `EM_ANALISE = 1`, `AGUARDANDO_ESTOQUE = 2`, `APROVADO_RETIRADA = 3`, `DEFERIDO_ENTREGUE = 4`, `INDEFERIDO = 5` |
| `parecer_tecnico` | `TextField(blank=True)` | Preenchido pela equipe da ADEFAL |
| `data_vencimento_emprestimo` | `DateField(null=True, blank=True)` | Definida quando `status = DEFERIDO_ENTREGUE` |
| `acao_devolucao` | `CharField` com `TextChoices` | `NENHUMA`, `RENOVACAO_SOLICITADA`, `DEVOLUCAO_CONFIRMADA` |
| `justificativa_renovacao` | `TextField(blank=True)` | Obrigatória ao solicitar renovação |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |
| `atualizado_em` | `DateTimeField(auto_now=True)` | |

### `EventoLinhaTempoEquipamento`

| Campo | Tipo | Regras |
|---|---|---|
| `solicitacao` | `ForeignKey(SolicitacaoEquipamento, on_delete=PROTECT, related_name="eventos")` | Obrigatório |
| `status` | `IntegerField` com `IntegerChoices` | Etapa registrada |
| `descricao` | `CharField(max_length=250)` | Obrigatório |
| `registrado_por` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT)` | |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

## Exceções (`equipamentos/exceptions.py`)

- `AnexoInvalido`: extensão não permitida, cabeçalho de bytes (magic bytes) incompatível com PDF/JPEG/PNG ou tamanho acima do limite (10 MB para laudo, 5 MB para comprovante).
- `SolicitacaoEquipamentoNaoEncontrada`: protocolo inexistente ou usuário sem permissão de acesso.
- `OperacaoEmprestimoInvalida`: tentativa de solicitar renovação sem justificativa ou em solicitação que não está entregue em empréstimo.

## `EquipamentoService` (`equipamentos/services/`)

| Método | Regra |
|---|---|
| `validar_arquivo_anexo(arquivo, tamanho_max_mb)` | Verifica se a extensão é `.pdf`, `.jpg`, `.jpeg` ou `.png`, se `arquivo.size <= tamanho_max_mb * 1024 * 1024` e se os primeiros bytes correspondem às assinaturas `%PDF-`, `\xff\xd8\xff` (JPEG) ou `\x89PNG\r\n\x1a\n` (PNG); caso contrário levanta `AnexoInvalido` |
| `criar_solicitacao(solicitante, ...)` | Valida permissão sobre o beneficiário PCD, valida laudo (10 MB) e comprovante de residência (5 MB), gera protocolo `EQP-AAAAMMDD-XXXX`, salva com `status = EM_ANALISE` e cria o primeiro `EventoLinhaTempoEquipamento` |
| `atualizar_status_triagem(operador_staff, protocolo, novo_status, parecer_tecnico="", data_vencimento=None)` | Restrito à equipe ADEFAL (`is_staff`). Atualiza o status, registra o evento na linha do tempo e notifica o titular |
| `obter_detalhe_e_linha_tempo(solicitante, protocolo)` | Verifica se `solicitante` é o beneficiário PCD, cuidador com vínculo `APROVADO` ou `is_staff`; caso contrário levanta `SolicitacaoEquipamentoNaoEncontrada` |
| `obter_anexo_protegido(solicitante, protocolo, tipo_documento)` | Verifica autorização estrita ([ADR 0005](../adr/0005-armazenamento-e-validacao-de-anexos.md)) e retorna o arquivo para resposta autenticada |
| `listar_alertas_vencimento(beneficiario_pcd, data_referencia=None)` | Retorna empréstimos vigentes cujo `data_vencimento_emprestimo` esteja a 7 dias ou menos (destacando marcos de 7 dias e 2 dias) |
| `registrar_renovacao_ou_devolucao(solicitante, protocolo, acao, justificativa="")` | Para `RENOVACAO_SOLICITADA`, exige justificativa preenchida; para `DEVOLUCAO_CONFIRMADA`, registra agendamento de vistoria no almoxarifado e cria evento na linha do tempo |

## Rotas (`app_name = "equipamentos"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/equipamentos/` | `equipamentos:lista` | `EquipamentoListView` | GET | Titular PCD ou Cuidador vinculado |
| `/equipamentos/solicitar/` | `equipamentos:solicitar` | `EquipamentoCreateView` | GET, POST | Titular PCD ou Cuidador vinculado |
| `/equipamentos/<str:protocolo>/` | `equipamentos:detalhe` | `EquipamentoDetailView` | GET | Titular PCD, Cuidador vinculado ou Staff |
| `/equipamentos/<str:protocolo>/anexo/<str:tipo_documento>/` | `equipamentos:baixar_anexo` | `EquipamentoAnexoDownloadView` | GET | Titular PCD, Cuidador vinculado ou Staff |
| `/equipamentos/<str:protocolo>/prazo/` | `equipamentos:gerenciar_prazo` | `EquipamentoPrazoView` | POST | Titular PCD ou Cuidador vinculado |

## Admin

`SolicitacaoEquipamentoAdmin` permite à equipe da ADEFAL visualizar as solicitações e executar ações que delegam para `EquipamentoService.atualizar_status_triagem`, mantendo a criação direta desabilitada no Admin.

## Testes

- [ ] Submissão válida com PDF/JPG/PNG cria solicitação `EM_ANALISE`, gera protocolo `EQP-AAAAMMDD-XXXX` e registra evento inicial na linha do tempo.
- [ ] Arquivo com extensão `.exe`/`.sh` ou arquivo `.pdf` falso (com conteúdo de script/texto sem cabeçalho `%PDF-`) é rejeitado com `AnexoInvalido` (`RS008`).
- [ ] Laudo acima de 10 MB ou comprovante acima de 5 MB é rejeitado com `AnexoInvalido`.
- [ ] Download de laudo médico (`EquipamentoAnexoDownloadView`) funciona para o titular PCD, seu cuidador vinculado e `is_staff`, mas retorna 404 para outros usuários autenticados e redireciona visitantes (`RS001`).
- [ ] A evolução de status pela triagem da ADEFAL atualiza a linha do tempo consultada pelo titular e pelo cuidador.
- [ ] Empréstimos a 7 dias e a 2 dias do vencimento geram alertas de devolução, permitindo solicitar renovação (com justificativa obrigatória) ou confirmar devolução.

