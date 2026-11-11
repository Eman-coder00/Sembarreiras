# Estado atual

Atualizado em: 2026-11-10

Este arquivo guarda apenas o que não está em outro lugar. Mantenha-o com cerca de 30 linhas e retire o que estiver resolvido. O status de cada documento fica no próprio documento, e o histórico fica no Git.

## Em andamento

- Todas as especificações ([Spec 0001](specs/0001-fundacao.md) a [Spec 0007](specs/0007-dados-iniciais.md)) foram implementadas nos 5 apps (`contas`, `emergencia`, `transporte`, `agendamentos`, `equipamentos`), cobrindo as 20 telas do protótipo e a suíte de testes automatizados.

## Próximos passos

1. Executar `python manage.py migrate` e `python manage.py carregar_dados_iniciais` no banco PostgreSQL local configurado no `.env`.
2. Iniciar o servidor local com `python manage.py runserver` para validação visual das 20 telas.

## Pendências

- Configurar credenciais do banco PostgreSQL local no arquivo `sistema/.env` (a partir de `sistema/.env.example`) para uso fora da suíte de testes.
