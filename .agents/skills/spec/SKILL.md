---
name: spec
description: Como escrever especificações de funcionalidade neste projeto. Use ao criar ou alterar uma spec em docs/specs/, ou antes de implementar uma funcionalidade que ainda não tem spec.
---

# Spec

Uma spec diz como uma funcionalidade será construída, com detalhes suficientes para implementá-la sem adivinhar. O que o produto deve fazer fica no PRD (`docs/prd/`), e o motivo das decisões estruturais, nos ADRs (`docs/adr/`).

## Quando escrever

- Escreva a spec antes do código, para toda funcionalidade nova.
- Altere a spec no mesmo trabalho em que o comportamento mudar, para que ela não contradiga o código.
- Correções pequenas, que apenas fazem o código cumprir a spec, não exigem alteração.

## Arquivo

Caminho: `docs/specs/NNNN-titulo-em-kebab-case.md`, com o próximo número livre de 4 dígitos. A numeração indica a ordem de implementação: uma spec só depende de specs com número menor.

## Modelo

Inclua apenas as seções que se aplicam à funcionalidade.

```markdown
# Spec NNNN: Título

- **Status:** Proposto
- **Requisitos:** RF-xx do [PRD NNNN](../prd/arquivo.md)
- **Decisões:** [ADR NNNN](../adr/arquivo.md)
- **Depende de:** [Spec NNNN](arquivo.md)

## Modelo `Nome`
Tabela com campo, tipo e regras, além de constraints e índices.

## `NomeService`
Tabela com método e regra, incluindo as exceções de domínio.

## Form

## Rotas (`app_name = "nome"`)
Tabela com rota, nome, view, métodos e acesso.

## Comportamento
O fluxo de cada view, inclusive os caminhos de erro.

## Admin

## Testes
- [ ] Comportamento verificável.
```

Omita as linhas de cabeçalho que não se aplicarem, como **Requisitos** em uma funcionalidade sem RF no PRD.

## Status

- `Proposto`: a spec ainda não foi implementada por completo.
- `Implementado`: o código e os testes cumprem a spec.

Marque um item de teste com `[x]` somente quando existir um teste que o cubra e a suíte estiver passando.

## Regras

- Siga `docs/arquitetura.md`: cada regra de negócio é especificada no service, nunca na view ou no template.
- Cite os requisitos atendidos. Se a funcionalidade mudar o que o produto faz e o requisito não existir, atualize o PRD primeiro.
- Se a spec exigir uma decisão difícil de reverter, escreva antes um ADR. Não repita o raciocínio dele aqui.
- Descreva contratos, como campos, assinaturas, rotas e erros. Inclua código apenas quando ele esclarecer uma regra.
- Cubra nos testes os caminhos de erro e, nas rotas protegidas, os casos de visitante, dono e outro usuário.
- Registre os limites aceitos, como condições de corrida toleradas nesta versão.
- Ao criar a spec, adicione o link dela no campo **Especificações** do PRD.
