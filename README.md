# SemBarreiras (MobiLivre — ADEFAL)

Plataforma web mobile-first desenvolvida em **Python + Django** com banco de dados **PostgreSQL**, voltada à autonomia, mobilidade urbana acessível e assistência em saúde de Pessoas com Deficiência Física (PCD) atendidas pela **ADEFAL** (Associação dos Deficientes Físicos de Alagoas) e seus cuidadores.

---

## Principais Módulos

- **`contas`**: cadastro de titular PCD (validação de CPF e CEP local), login por perfil (`PCD` ou `CUIDADOR`) com bloqueio temporário após 5 falhas, vínculo de cuidador via código OTP, recuperação de senha, preferências de acessibilidade motora (WCAG 2.1 AA), inativação LGPD, Home dinâmica por perfil e Central de Notificações (`/notificacoes/`).
- **`emergencia`**: até 3 contatos prioritários, botão de pânico com cache offline (`localStorage`), contagem regressiva de 5 segundos com cancelamento seguro, disparo com coordenadas GPS / fallback SMS e histórico auditável.
- **`transporte`**: mapa acessível interativo (`/transporte/mapa/`) com pontos de parada e unidades ADEFAL, filtragem exclusiva de ônibus com acessibilidade física ativa (`acessibilidade_ativa=True`), distância em metros e previsão de chegada (ETA).
- **`agendamentos`**: agendamento de consultas na ADEFAL com trava de antecedência de 24h (cancelamento/remarcação), transporte hospitalar adaptado porta a porta (antecedência mínima de 48h e saldo de vagas na frota), comprovante digital com assinatura `HMAC-SHA256` e validação na portaria (`is_staff`).
- **`equipamentos`**: solicitação de empréstimo de equipamentos com medidas antropométricas, validação binária (*magic bytes*) e tamanho de laudos/comprovantes, download autenticado protegido, linha do tempo de triagem e alertas de vencimento (7 dias e 2 dias) com renovação/devolução.

---

## Documentação e Arquitetura

- [Pilares de Programação Orientada a Objetos (POO - AV03)](docs/poo.md)
- [Estrutura de Banco de Dados — Entrega 3AF (5,0 Pontos)](docs/entrega_3af_banco_de_dados.md)
- [Script do Banco de Dados PostgreSQL (DDL Completo - 3AF)](docs/sem_barreiras.sql)
- [Visão de Arquitetura (MVT + Camada de Service)](docs/arquitetura.md)
- [PRD — Requisitos do Sistema](docs/prd.md)
- [Decisões de Arquitetura (ADRs)](docs/adr/0001-mvt-com-camada-de-service.md)
- [Especificações Técnicas (Specs 0001 a 0007)](docs/specs/0001-fundacao.md)

---

## Pré-requisitos

- **Python 3.12+**
- **PostgreSQL 14+** instalado e em execução na porta `5432`
- **Git**

---

## Como Copiar e Executar Localmente

### 1. Clonar o repositório

```powershell
git clone https://github.com/Eman-coder00/Sembarreiras.git
cd Sembarreiras
```

### 2. Criar ambiente virtual e instalar dependências

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente (`.env`)

Copie o arquivo modelo [`.env.example`](.env.example) para `.env`:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

> Caso sua senha do PostgreSQL não seja a padrão `postgres`, abra o arquivo `.env` e ajuste `POSTGRES_USER` e `POSTGRES_PASSWORD`.

### 4. Criar o banco de dados PostgreSQL

Execute o utilitário [`criar_banco.py`](criar_banco.py) para criar automaticamente o banco `sem_barreiras` no seu PostgreSQL:

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe criar_banco.py
```

**Linux / macOS:**
```bash
.venv/bin/python criar_banco.py
```

### 5. Aplicar migrações e carregar dados iniciais

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py carregar_dados_iniciais
```

**Linux / macOS:**
```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py carregar_dados_iniciais
```

*(O comando `carregar_dados_iniciais` é idempotente e popula os CEPs de Maceió/AL, paradas acessíveis, linhas de ônibus, veículos adaptados, vagas de consultas na grade da ADEFAL e a frota de vans).*

### 6. Executar os testes automatizados

Para verificar a integridade da aplicação e conformidade com as regras de negócio:

```powershell
.\.venv\Scripts\python.exe manage.py test
```

### 7. Iniciar o servidor de desenvolvimento

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Acesse no navegador: **http://127.0.0.1:8000/**

---

## Perfis de Acesso e Como Testar as Funcionalidades

1. **Acesso do Titular PCD:**
   - Acesse **Cadastre-se como Titular PCD** (`/cadastro/pcd/`).
   - Informe dados com CEP de Maceió (ex: `57051-190` - preenchimento automático da ADEFAL) e defina sua senha com botão de visualização do olho.
   - Na tela inicial, teste: **Botão de Pânico** (contagem regressiva de 5s e cancelamento), **Mapa Acessível** (rotas de ônibus com rampa ativa), **Agendamento de Consultas** com transporte de van adaptada e **Solicitação de Cadeiras de Rodas/Órteses** com upload de fotos.

2. **Acesso do Cuidador / Tutor Legal:**
   - Acesse **Vincular como Cuidador** (`/cadastro/cuidador/`).
   - Solicite o vínculo informando o CPF do titular PCD; confirme o vínculo através do código **OTP de 6 dígitos** emitido para o titular.

3. **Acesso Administrativo / Portaria e Triagem ADEFAL:**
   - Crie uma conta de equipe com:
     ```powershell
     .\.venv\Scripts\python.exe manage.py createsuperuser
     ```
   - Faça login para validar QR Codes de agendamentos na recepção (`/agendamentos/portaria/validar/`) e aprovar laudos médicos de equipamentos.

