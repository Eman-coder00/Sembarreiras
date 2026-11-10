---
name: prd
description: Como escrever requisitos de produto neste projeto. Use ao criar ou alterar um PRD em docs/prd/, ou ao adicionar, mudar ou retirar requisitos e itens fora do escopo.
---

# PRD

Um PRD descreve o que o produto faz, para quem e por quê. Como construir fica nas specs (`docs/specs/`) e nos ADRs (`docs/adr/`).

## Quando escrever

- Crie um PRD para um produto ou uma nova versão com objetivo próprio.
- Altere o PRD existente quando o comportamento esperado do produto mudar.
- Mudanças internas, sem efeito para quem usa, não entram no PRD.

## Arquivo

Caminho: `docs/prd/NNNN-titulo-em-kebab-case.md`, com o próximo número livre de 4 dígitos.

## Modelo

```markdown
# PRD NNNN: Título

- **Status:** Proposto
- **Data:** AAAA-MM-DD
- **Especificações:** links para as specs

## Objetivo

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|

## Requisitos funcionais

### Área

- **RF-01:** Comportamento observável.

## Requisitos não funcionais

- **RNF-01 (tema):** Qualidade exigida.

## Fora do escopo desta versão

## Critérios de conclusão
```

## Status

- `Proposto`: aguardando a decisão da pessoa responsável. Um agente sempre cria o PRD com este status.
- `Aceito`: os requisitos estão valendo.

## Regras

- Escreva requisitos verificáveis: cada um precisa poder virar ao menos um teste. Prefira "A listagem mostra 10 posts por página" a "A listagem é fácil de usar".
- Nomeie o perfil e o comportamento, sem citar tabelas, classes, rotas ou bibliotecas.
- Mantenha um único comportamento em cada requisito.
- Não renumere nem reaproveite `RF-xx` e `RNF-xx`, pois as specs os citam. Requisitos novos recebem o próximo número.
- Registre em "Fora do escopo" o que alguém poderia supor incluído.
- Não invente requisitos. Se o pedido não definir um comportamento importante, pergunte à pessoa responsável.
- Ao alterar requisitos, atualize as specs que os citam.
