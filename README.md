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

- [Visão de Arquitetura (MVT + Camada de Service)](docs/arquitetura.md)
- [PRD 0001 — Requisitos do Sistema](docs/prd/0001-sem-barreiras.md)
- [Decisões de Arquitetura (ADRs)](docs/adr/0001-mvt-com-camada-de-service.md)
- [Especificações Técnicas (Specs 0001 a 0007)](docs/specs/0001-fundacao.md)

---

## Pré-requisitos

- **Python 3.12+**
- **PostgreSQL** instalado e em execução na porta `5432`
- **Git**

---

## Como Copiar e Executar Localmente

### 1. Clonar o repositório

```powershell
git clone <URL_DO_REPOSITORIO>
cd <NOME_DA_PASTA>
```

> Caso o repositório contenha a pasta `sistema/` na raiz, entre nela antes dos passos seguintes:
> ```powershell
> cd sistema
> ```

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

Edite o `.env` e informe o usuário e a senha do seu PostgreSQL local (`POSTGRES_USER` e `POSTGRES_PASSWORD`).

### 4. Criar o banco de dados PostgreSQL

Execute o utilitário [`criar_banco.py`](criar_banco.py) para criar automaticamente o banco `sem_barreiras` caso ainda não exista:

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\python.exe criar_banco.py
```

**Linux / macOS:**
```bash
.venv/bin/python criar_banco.py
```

### 5. Aplicar migrações e carregar os dados iniciais

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

*(O comando `carregar_dados_iniciais` é idempotente e popula CEPs de Maceió/AL, linhas e paradas acessíveis, ônibus adaptados, vagas na agenda da ADEFAL e frota de vans).*

### 6. (Opcional) Criar usuário administrador / equipe ADEFAL

Para acessar `/admin/`, validar QR Codes na portaria e realizar triagem de equipamentos:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

### 7. Executar os testes automatizados

```powershell
.\.venv\Scripts\python.exe manage.py test
```

### 8. Iniciar o servidor de desenvolvimento

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Acesse no navegador: **http://127.0.0.1:8000/**

