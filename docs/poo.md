# Pilares de Programação Orientada a Objetos (POO)

Este documento descreve como os **4 Pilares da Programação Orientada a Objetos** foram aplicados no projeto **SemBarreiras (MobiLivre — ADEFAL)**, atendendo integralmente ao critério de avaliação da disciplina (60% da nota da AV03).

---

## 1. Abstração

A **Abstração** consiste em isolar aspectos essenciais do domínio da ADEFAL, ocultando detalhes irrelevantes e modelando entidades do mundo real em classes especializadas com responsabilidades bem definidas:

* **Modelos de Dados do Domínio (`models/`)**:
  - `Usuario`: abstração unificada de usuários que representam tanto o titular PCD quanto o cuidador.
  - `PerfilPCD`: abstração das características antropométricas, tipo de deficiência motora e preferências de acessibilidade.
  - `Consulta` e `VagaAgendaADEFAL`: abstração da grade de horários e sessões de reabilitação médica.
  - `SolicitacaoTransporte` e `VeiculoAdaptado`: abstração da logística de vans com plataforma elevatória e linhas urbanas.
  - `SolicitacaoEquipamento` e `EventoLinhaTempoEquipamento`: abstração do ciclo de vida de órteses e cadeiras de rodas do acervo.
* **Camada de Serviços (`services/`)**:
  - Abstrai processos complexos de negócio em interfaces limpas e reutilizáveis (`ContaService`, `PanicoService`, `TransporteUrbanoService`, `AgendamentoService`, `EquipamentoService`), permitindo que a aplicação realize cálculos como distância Haversine, assinatura criptográfica HMAC-SHA256 e validação binária de arquivos sem expor a complexidade interna.

---

## 2. Encapsulamento

O **Encapsulamento** protege o estado interno dos objetos e garante que alterações e consultas ocorram exclusivamente por operações controladas e validadas:

* **Isolamento de Regras de Negócio na Camada de Service**:
  - As *Views* nunca acessam o banco de dados diretamente nem aplicam regras de domínio.
  - A integridade dos dados é protegida por transações atômicas (`transaction.atomic()`).
  - Métodos auxiliares privados iniciados com `_` (ex: `_buscar_usuario_por_identificador`, `_obter_ip`, `_calcular_distancia`) protegem algoritmos internos contra chamadas indevidas de fora do módulo.
* **Proteção e Imutabilidade de Dados Sensíveis**:
  - O CPF do usuário é blindado contra alterações após o cadastro.
  - O acesso a arquivos médicos anexados (laudos e comprovantes de residência) é restrito através de controle de autorização nos services, impedindo acesso via URL direta.

---

## 3. Herança

A **Herança** foi utilizada para promover o reuso de código, padronizar comportamentos e estabelecer hierarquias taxonômicas claras:

* **Hierarquia de Classes em Views**:
  - Todas as views do sistema herdam diretamente da classe base `django.views.View` (`class EntrarView(View):`, `class ConsultaCreateView(LoginRequiredMixin, View):`).
  - Reuso de controle de autenticação via herança múltipla com o mixin `LoginRequiredMixin`.
* **Hierarquia de Modelos ORM**:
  - Todos os modelos herdam da classe base `django.db.models.Model`.
  - A entidade `Usuario` herda de `AbstractBaseUser` e `PermissionsMixin`, incorporando mecanismos de senha hash, permissões e autenticação padrão do framework.
* **Hierarquia de Exceções de Domínio**:
  - Exceções especializadas herdando de classes base customizadas e da classe raiz `Exception`:
    - `ContaException` -> `CpfJaCadastrado`, `CredenciaisInvalidas`, `ContaTemporariamenteBloqueada`, `SenhaAtualInvalida`.
    - `VinculoException` -> `VinculoInvalido`, `PermissaoNegadaTitular`.
    - `EquipamentoException` -> `AnexoInvalido`, `OperacaoEmprestimoInvalida`.

---

## 4. Polimorfismo

O **Polimorfismo** permite que diferentes classes implementem comportamentos específicos através de interfaces comuns:

* **Sobrescrita de Métodos em Views (`get` e `post`)**:
  - Cada classe de View sobrescreve polimorficamente os métodos `get(self, request, *args, **kwargs)` e `post(self, request, *args, **kwargs)` da classe ancestral `View`, tratando as requisições HTTP de forma personalizada para cada tela.
* **Comportamento Polimórfico de Acesso (Titular PCD vs Cuidador)**:
  - Métodos como `ContaService.obter_titular_autorizado(usuario, titular_cpf)` respondem polimorficamente dependendo do papel do usuário logado: se for titular PCD, retorna os dados diretamente; se for cuidador, valida o vínculo aprovado com o titular solicitado antes de liberar a operação.
* **Sobrescrita de Métodos de Formulários (`clean`)**:
  - Formulários sobrescrevem o método `clean()` e `clean_<campo>()` para implementar validações cruzadas e de formato específico para cada formulário do sistema.
