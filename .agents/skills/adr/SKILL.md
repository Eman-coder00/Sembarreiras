---
name: adr
description: Como escrever decisões de arquitetura neste projeto. Use ao criar, aceitar ou substituir um ADR em docs/adr/, ou quando uma mudança contrariar ou exigir uma decisão de arquitetura.
---

# ADR

Um ADR registra uma decisão e o motivo dela, para que ninguém precise adivinhar depois. As regras do dia a dia ficam em `docs/arquitetura.md`, e o ADR explica por que elas existem.

## Quando escrever

Escreva um ADR quando a decisão for difícil de reverter, tiver alternativas reais ou afetar várias partes do projeto, como escolher banco de dados, formato de conteúdo ou uma nova dependência estrutural.

Não escreva para escolhas locais e fáceis de trocar, nem para detalhes de uma funcionalidade, que ficam na spec.

Se uma mudança contrariar um ADR aceito, pare e proponha um novo ADR antes de alterar o código.

## Arquivo

- Caminho: `docs/adr/NNNN-titulo-em-kebab-case.md`.
- Use o próximo número livre, com 4 dígitos. Não reaproveite números.
- Um ADR trata de uma única decisão.

## Modelo

```markdown
# ADR NNNN: Título da decisão

- **Status:** Proposto
- **Data:** AAAA-MM-DD

## Contexto

O problema, as restrições e as alternativas que importam.

## Decisão

O que foi decidido, de forma afirmativa e verificável.

## Consequências

- Os ganhos e também os custos aceitos.
```

## Status

- `Proposto`: aguardando a decisão da pessoa responsável. Um agente sempre cria o ADR com este status.
- `Aceito`: a decisão está valendo.
- `Substituído por [ADR NNNN](arquivo.md)`: a decisão deixou de valer.

## Regras

- Não reescreva a decisão de um ADR aceito. Crie outro ADR e altere apenas o status do antigo.
- Registre em Consequências ao menos um custo. Se não houver custo nem alternativa, provavelmente não é preciso um ADR.
- Escreva no presente, sem narrar a discussão que levou à decisão.
- Use links relativos para os ADRs, specs e PRDs relacionados.
- Atualize `docs/arquitetura.md` e as specs afetadas quando a decisão mudar uma regra.
