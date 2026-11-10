# Estado atual

Atualizado em: 2026-11-10

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- Planejamento documental concluído: [PRD 0001](prd/0001-sem-barreiras.md) e [ADRs 0001 a 0005](adr/0001-mvt-com-camada-de-service.md) aceitos, e especificações técnicas ([Spec 0001](specs/0001-fundacao.md) a [Spec 0007](specs/0007-dados-iniciais.md)) criadas.

## Próximos passos

1. Implementar a [Spec 0001: Fundação do projeto](specs/0001-fundacao.md) (`manage.py`, `core/`, estrutura dos 5 apps, `templates/base.html` e `test_arquitetura.py`).
2. Implementar a [Spec 0002: Contas, vínculo de cuidador e acessibilidade motora](specs/0002-contas-vinculo-e-acessibilidade.md).
3. Implementar a [Spec 0003: Emergência e botão de pânico](specs/0003-emergencia-botao-panico.md).
4. Implementar a [Spec 0004: Transporte urbano acessível](specs/0004-transporte-urbano-acessivel.md).
5. Implementar a [Spec 0005: Agendamentos na ADEFAL e transporte hospitalar adaptado](specs/0005-agendamentos-e-transporte-hospitalar.md).
6. Implementar a [Spec 0006: Empréstimo de equipamentos de apoio e validação de laudos](specs/0006-equipamentos-e-laudos.md).
7. Implementar a [Spec 0007: Dados iniciais de demonstração](specs/0007-dados-iniciais.md).

## Pendências

- Configurar banco PostgreSQL local (`.env` a partir do `.env.example`) ao iniciar a implementação da Spec 0001.
