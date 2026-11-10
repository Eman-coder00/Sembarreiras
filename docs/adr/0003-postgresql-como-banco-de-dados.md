# ADR 0003: PostgreSQL como banco de dados e política de inativação lógica

- **Status:** Aceito
- **Data:** 2026-11-10

## Contexto

O SemBarreiras lida com operações concorrentes (acionamentos de emergência, reservas simultâneas de vagas em consultas e vans adaptadas da ADEFAL) e exige integridade transacional rigorosa (`UniqueConstraint`, `CheckConstraint` e bloqueio de linhas em reservas), além de preservação de histórico para auditoria médica e conformidade com a LGPD quando um titular solicita a desativação da conta ([PRD 0001](../prd/0001-sem-barreiras.md)).

O SQLite limita escritas simultâneas, enquanto o PostgreSQL oferece suporte completo a concorrência, transações isoladas e constraints relacionais robustas.

## Decisão

- Utilizar **PostgreSQL** como banco de dados do projeto, conectado via `psycopg` e configurado por variáveis de ambiente (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`).
- Acessar o banco exclusivamente pelo ORM do Django, mantendo consultas portáveis e usando `transaction.atomic()` nos services que realizam escritas dependentes ou controle de vagas.
- Proibir a exclusão física de contas de usuários, ocorrências de emergência, agendamentos e solicitações de equipamentos: a desativação de conta altera o status para `INATIVO` e mascara os dados identificáveis diretos no service, preservando o vínculo estatístico e de auditoria.

## Consequências

- Maior fidelidade ao ambiente de produção e suporte nativo a concorrência nas reservas de vagas da ADEFAL e no registro de emergências.
- Exige uma instância do PostgreSQL em execução (local ou via container) e configuração das variáveis de ambiente no `.env` para rodar o projeto e a suíte de testes, além da dependência `psycopg[binary]` no `requirements.txt`.
- Os services de listagem e autenticação devem sempre filtrar registros inativos, garantindo que contas desativadas não acessem o sistema nem recebam notificações.

