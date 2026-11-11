# Spec 0002: Contas, vínculo de cuidador e acessibilidade motora

- **Status:** Implementado
- **Requisitos:** RF-01 a RF-06, RNF-02, RNF-03 e RNF-04 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0002](../adr/0002-modelo-de-usuario-e-perfis-de-acesso.md), [ADR 0003](../adr/0003-postgresql-como-banco-de-dados.md), [ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)
- **Depende de:** [Spec 0001](0001-fundacao.md)

## Modelos (`contas/models/`)

### `Usuario` (herda de `AbstractUser`)

| Campo | Tipo | Regras |
|---|---|---|
| `cpf` | `CharField(max_length=14, unique=True)` | Obrigatório, formato `XXX.XXX.XXX-XX`, validado por dígitos verificadores e imutável após criação |
| `nome_completo` | `CharField(max_length=120)` | Obrigatório, mínimo de 3 caracteres |
| `email` | `EmailField(max_length=200, unique=True)` | Obrigatório |
| `telefone` | `CharField(max_length=15)` | Obrigatório, formato `(XX) 9XXXX-XXXX` |
| `data_nascimento` | `DateField(null=True, blank=True)` | Obrigatório para perfil PCD |
| `papel` | `CharField` com `TextChoices` | `PCD` (`"PCD"`, Usuário PCD Física) ou `CUIDADOR` (`"CUIDADOR"`, Cuidador / Tutor Legal) |
| `status_cadastro` | `IntegerField` com `IntegerChoices` | `ATIVO = 1`, `INATIVO = 2`, `BLOQUEADO = 3` (padrão `ATIVO`) |
| `tentativas_login_falhas` | `PositiveSmallIntegerField(default=0)` | Incrementado a cada falha de senha |
| `bloqueado_ate` | `DateTimeField(null=True, blank=True)` | Preenchido com `now() + 15 min` ao atingir 5 falhas consecutivas |
| `versao_sessao` | `PositiveIntegerField(default=1)` | Incrementado ao redefinir senha para invalidar sessões anteriores |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

### `PerfilPCD`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `OneToOneField(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="perfil_pcd")` | Obrigatório |
| `tipo_deficiencia` | `CharField` com `TextChoices` | `CADEIRANTE`, `MOBILIDADE_MEMBROS_INFERIORES`, `LIMITACAO_MEMBROS_SUPERIORES` |
| `equipamentos_apoio` | `CharField(max_length=200)` | Lista separada por vírgula dos itens selecionados (`CADEIRA_MANUAL`, `CADEIRA_MOTORIZADA`, `PROTESE`, `MULETA_BENGALA`, `ANDADOR`, `NENHUM`) |
| `tamanho_toque` | `CharField` com `TextChoices` | `PADRAO` (padrão), `EXPANDIDO`, `MAXIMO` |
| `timeout_tela` | `CharField` com `TextChoices` | `PADRAO` (padrão), `PROLONGADO_10M` |
| `alto_contraste` | `BooleanField(default=False)` | |
| `cep` | `CharField(max_length=9)` | Formato `XXXXX-XXX`, obrigatório |
| `logradouro` | `CharField(max_length=100)` | Obrigatório |
| `numero` | `CharField(max_length=10)` | Obrigatório |
| `complemento` | `CharField(max_length=100, blank=True)` | Opcional |
| `bairro` | `CharField(max_length=100)` | Obrigatório |
| `municipio` | `CharField(max_length=100)` | Obrigatório |
| `uf` | `CharField(max_length=2)` | Obrigatório |

### `VinculoCuidador`

| Campo | Tipo | Regras |
|---|---|---|
| `cuidador` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="vinculos_como_cuidador")` | Obrigatório |
| `titular_pcd` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="vinculos_cuidadores")` | Obrigatório |
| `grau_parentesco` | `CharField` com `TextChoices` | `MAE_PAI`, `TUTOR_LEGAL`, `CUIDADOR_PROFISSIONAL`, `CONJUGE`, `OUTRO` |
| `codigo_otp` | `CharField(max_length=6)` | Gerado com `secrets` |
| `status` | `IntegerField` com `IntegerChoices` | `PENDENTE = 1`, `APROVADO = 2`, `REVOGADO = 3` |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |
| `atualizado_em` | `DateTimeField(auto_now=True)` | |

No `Meta`: `UniqueConstraint` em `(cuidador, titular_pcd)`.

### `TokenRecuperacaoSenha`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="tokens_recuperacao")` | Obrigatório |
| `codigo` | `CharField(max_length=6)` | Numérico de 6 dígitos gerado com `secrets` |
| `expira_em` | `DateTimeField` | `now() + 15 minutos` |
| `utilizado` | `BooleanField(default=False)` | |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

### `LogAuditoriaConta`

| Campo | Tipo | Regras |
|---|---|---|
| `usuario` | `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="logs_auditoria")` | Obrigatório |
| `evento` | `CharField(max_length=60)` | Ex.: `LOGIN_SUCESSO`, `LOGIN_FALHA`, `ALTERACAO_DADOS_CRITICOS`, `VINCULO_APROVADO`, `VINCULO_REVOGADO`, `REDEFINICAO_SENHA`, `INATIVACAO_LGPD` |
| `detalhes` | `TextField(blank=True)` | Sem registrar senhas nem tokens secretos |
| `ip` | `CharField(max_length=45, blank=True)` | |
| `criado_em` | `DateTimeField(auto_now_add=True)` | |

### `CepLocal`

Base local de CEPs para consulta rápida sem internet ([ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)): `cep` (`CharField(max_length=9, unique=True)`), `logradouro`, `bairro`, `municipio` e `uf`.

## Exceções (`contas/exceptions.py`)

- `CpfJaCadastrado`: CPF já existe na base.
- `EmailJaCadastrado`: e-mail já existe na base.
- `CepNaoLocalizado`: CEP não encontrado na base local (libera preenchimento manual).
- `CredenciaisInvalidas`: identificador, perfil ou senha incorretos.
- `ContaTemporariamenteBloqueada`: conta em período de bloqueio de 15 minutos ou com status `BLOQUEADO`.
- `SenhaAtualInvalida`: reautenticação falhou ao tentar alterar telefone ou endereço.
- `VinculoInvalido`: titular PCD não encontrado/inativo, código OTP inválido ou vínculo não pertence ao usuário.
- `TokenRecuperacaoInvalido`: código de recuperação inexistente, já utilizado ou expirado (> 15 min).
- `PermissaoNegadaTitular`: usuário não é o titular PCD nem cuidador com vínculo `APROVADO` para o titular.

## Services (`contas/services/`)

### `ContaService`

| Método | Regra |
|---|---|
| `consultar_cep(cep)` | Retorna dicionário de endereço a partir de `CepLocal` ou levanta `CepNaoLocalizado` |
| `cadastrar_pcd(...)` | Valida unicidade de CPF e e-mail, cria `Usuario(papel="PCD")` com hash de senha e `PerfilPCD` em `transaction.atomic()` |
| `atualizar_dados_pcd(usuario, senha_atual, ...)` | Se telefone ou endereço mudarem, exige `usuario.check_password(senha_atual)` (ou levanta `SenhaAtualInvalida`) e grava `LogAuditoriaConta`. Nunca altera o CPF |
| `inativar_conta_lgpd(usuario, senha_atual)` | Valida `senha_atual`, altera `status_cadastro = INATIVO`, `is_active = False` e mascara nome, e-mail, telefone e endereço preservando o ID para auditoria |
| `atualizar_acessibilidade(usuario, ...)` | Atualiza `tipo_deficiencia`, `equipamentos_apoio`, `tamanho_toque`, `timeout_tela` e `alto_contraste` no `PerfilPCD` |
| `obter_titular_autorizado(solicitante, titular_cpf=None)` | Se `solicitante.papel == "PCD"`, retorna o próprio `solicitante`. Se for `CUIDADOR`, verifica vínculo `APROVADO` com o titular (ou levanta `PermissaoNegadaTitular`) |
| `listar_notificacoes(usuario)` | Reúne avisos gerais: disparos de pânico para cuidadores cadastrados nos contatos de emergência do titular, alerta de ausência de contatos para PCD, vínculos OTP pendentes, prazos/retiradas de equipamentos e próximas consultas confirmadas |
| `obter_resumo_home(usuario)` | Calcula o contexto dinâmico da Home adaptada por perfil (`PCD` ou `CUIDADOR`), contagem de notificações, alerta de pânico ao cuidador e texto de ação sugerida |

### `AutenticacaoService`

| Método | Regra |
|---|---|
| `autenticar(identificador, senha, perfil_selecionado, ip="")` | Busca usuário ativo por CPF ou e-mail. Se `bloqueado_ate > now()`, levanta `ContaTemporariamenteBloqueada`. Se a senha falhar, incrementa `tentativas_login_falhas` (bloqueando por 15 min na 5ª falha) e levanta `CredenciaisInvalidas`. Se o `papel` divergir de `perfil_selecionado`, levanta `CredenciaisInvalidas`. No sucesso, zera tentativas, registra log e retorna o `Usuario` |
| `solicitar_recuperacao_senha(identificador)` | Se localizar usuário ativo por CPF ou e-mail, cria `TokenRecuperacaoSenha` de 6 dígitos válido por 15 min e registra o envio simulado |
| `redefinir_senha(identificador, codigo, nova_senha)` | Valida token não utilizado e dentro dos 15 min, aplica `set_password(nova_senha)`, incrementa `versao_sessao`, limpa bloqueios e grava log |

### `VinculoCuidadorService`

| Método | Regra |
|---|---|
| `cadastrar_cuidador_e_solicitar_vinculo(...)` | Cria ou atualiza cuidador (`papel="CUIDADOR"`), localiza titular PCD ativo pelo CPF, gera `VinculoCuidador(status=PENDENTE)` com código OTP de 6 caracteres e registra notificação ao titular |
| `confirmar_vinculo(vinculo_id, codigo_otp, solicitante)` | Valida o código OTP, altera status para `APROVADO` e grava log de auditoria |
| `revogar_vinculo(vinculo_id, solicitante)` | Permite ao titular PCD ou ao próprio cuidador alterar o status para `REVOGADO` imediatamente |
| `listar_vinculos(usuario)` | Lista cuidadores vinculados (para PCD) ou titulares atendidos (para Cuidador) |

## Rotas (`app_name = "contas"`)

| Rota | Nome | View | Métodos | Acesso |
|---|---|---|---|---|
| `/` | `contas:home` | `HomeView` | GET | Autenticado |
| `/notificacoes/` | `contas:notificacoes` | `NotificacoesView` | GET | Autenticado |
| `/conta/` | `contas:painel` | `PainelInicialView` | GET | Autenticado |
| `/entrar/` | `contas:entrar` | `EntrarView` | GET, POST | Público |
| `/sair/` | `contas:sair` | `SairView` | POST | Autenticado |
| `/cadastro/pcd/` | `contas:cadastro_pcd` | `CadastroPCDView` | GET, POST | Público |
| `/cadastro/cuidador/` | `contas:cadastro_cuidador` | `CadastroCuidadorView` | GET, POST | Público |
| `/cep/consultar/` | `contas:consultar_cep` | `ConsultarCepView` | GET | Público |
| `/perfil/` | `contas:perfil` | `PerfilEditarView` | GET, POST | Autenticado (PCD) |
| `/perfil/acessibilidade/` | `contas:acessibilidade` | `AcessibilidadeView` | GET, POST | Autenticado (PCD) |
| `/perfil/inativar/` | `contas:inativar` | `ContaInativarView` | POST | Autenticado |
| `/vinculos/` | `contas:vinculos` | `VinculoListView` | GET | Autenticado |
| `/vinculos/<int:vinculo_id>/confirmar/` | `contas:confirmar_vinculo` | `VinculoConfirmarView` | POST | Autenticado |
| `/vinculos/<int:vinculo_id>/revogar/` | `contas:revogar_vinculo` | `VinculoRevogarView` | POST | Autenticado |
| `/senha/recuperar/` | `contas:recuperar_senha` | `SenhaRecuperarView` | GET, POST | Público |
| `/senha/redefinir/` | `contas:redefinir_senha` | `SenhaRedefinirView` | GET, POST | Público |

## Comportamento das Views principais

- **`HomeView`**: hub inicial pós-login que adapta dinamicamente a grade de atalhos conforme o perfil (`12` botões para Titular `PCD` e `9` botões para `CUIDADOR`), acendendo indicadores laranja para ações sugeridas e um alerta crítico quando um cuidador cadastrado nos contatos de emergência possui disparo de pânico recente do titular.
- **`NotificacoesView`**: central unificada de avisos gerais acionada pelo botão de notificações da Home (emergências ao cuidador, vínculos OTP pendentes, prazos de equipamentos e consultas confirmadas).
- **`EntrarView`**: exibe seletor de perfil em duas opções lado a lado (`PCD` ou `CUIDADOR`), identificador (CPF ou e-mail) e senha. No sucesso, chama `login(request, usuario)`, aplica `request.session.set_expiry(None)` caso "Manter conectado" não esteja marcado (ou expiração de 10 minutos se `timeout_tela == PROLONGADO_10M`) e redireciona para `contas:home`.
- **`VinculoListView`**: separa os papéis na tela de vínculos pendentes — o Titular PCD visualiza apenas o código OTP de autorização em destaque, enquanto o Cuidador visualiza o formulário para digitar o código e confirmar o vínculo.
- **`CadastroPCDView`**: valida CPF (dígitos verificadores), senha alfanumérica de no mínimo 8 caracteres e endereço; se o CEP não existir na base local, exibe "Endereço não localizado" e permite preenchimento manual.
- **`PerfilEditarView`**: mantém o CPF somente leitura e exige a senha atual ao alterar telefone ou endereço.

## Testes

- [x] Cadastro PCD com dados válidos cria usuário e perfil de acessibilidade; CPF inválido, CPF duplicado ou e-mail duplicado são rejeitados com as mensagens previstas.
- [x] Consulta de CEP existente preenche logradouro/bairro/município/UF; CEP inexistente retorna mensagem "Endereço não localizado" e permite preenchimento manual.
- [x] Login aceita CPF ou e-mail com o perfil correto e rejeita quando o perfil selecionado diverge do cadastro.
- [x] 5 tentativas consecutivas de senha incorreta bloqueiam a conta por 15 minutos (`ContaTemporariamenteBloqueada`).
- [x] Vínculo de cuidador nasce `PENDENTE`, exige o código OTP correto para passar a `APROVADO` e perde acesso imediatamente quando `REVOGADO`.
- [x] Alteração de acessibilidade motora atualiza as classes de área de toque e alto contraste renderizadas no `base.html`.
- [x] Alteração de telefone ou endereço exige senha atual e gera registro em `LogAuditoriaConta`; o CPF nunca é alterado.
- [x] Recuperação de senha com token válido de 6 dígitos dentro de 15 minutos redefine a senha e invalida token expirado ou já usado.
- [x] Inativação de conta altera status para `INATIVO`, mascara dados pessoais identificáveis e impede novo login.
- [x] `HomeView` exibe a grade adaptada ao perfil (`PCD` vs `CUIDADOR`) com os destaques dinâmicos de ação sugerida.
- [x] `NotificacoesView` exibe aviso crítico de Botão de Pânico na Home e em `/notificacoes/` para o cuidador vinculado cadastrado nos contatos de emergência do titular.

