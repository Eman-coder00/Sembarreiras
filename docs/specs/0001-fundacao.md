# Spec 0001: Fundação do projeto

- **Status:** Implementado
- **Requisitos:** RNF-01, RNF-02, RNF-03 e RNF-06 do [PRD 0001](../prd/0001-sem-barreiras.md)
- **Decisões:** [ADR 0001](../adr/0001-mvt-com-camada-de-service.md), [ADR 0002](../adr/0002-modelo-de-usuario-e-perfis-de-acesso.md), [ADR 0003](../adr/0003-postgresql-como-banco-de-dados.md)

Esta especificação deve ser implementada primeiro, e o modelo de usuário (`contas.Usuario`) precisa existir antes do primeiro `migrate`.

## Configurações (`core/settings.py`)

| Configuração | Valor |
|---|---|
| `INSTALLED_APPS` | Adicionar `"contas"`, `"emergencia"`, `"transporte"`, `"agendamentos"` e `"equipamentos"` |
| `SECRET_KEY` | Variável de ambiente `DJANGO_SECRET_KEY`. Sem ela, usa uma chave temporária com `DEBUG = True`. Com `DEBUG = False`, o Django levanta erro ao precisar da chave |
| `DATABASES["default"]` | `django.db.backends.postgresql` lendo `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT` do ambiente |
| `AUTH_USER_MODEL` | `"contas.Usuario"` |
| `LOGIN_URL` | `"contas:entrar"` |
| `LANGUAGE_CODE` | `"pt-br"` |
| `TIME_ZONE` | `"America/Maceio"` |
| `USE_TZ` | `True` |
| `TEMPLATES[0]["DIRS"]` | `[BASE_DIR / "templates"]` |
| `STATICFILES_DIRS` | `[BASE_DIR / "static"]` |
| `MEDIA_ROOT` | `BASE_DIR / "media"` (sem rota estática pública, conforme [ADR 0005](../adr/0005-armazenamento-e-validacao-de-anexos.md)) |

## Estrutura

```text
core/
  settings.py
  urls.py
contas/
  models/
  forms/
  services/
  views/
  templates/contas/
  tests/
  exceptions.py
  urls.py
emergencia/
  models/
  forms/
  services/
  views/
  templates/emergencia/
  tests/
  exceptions.py
  urls.py
transporte/
  models/
  forms/
  services/
  views/
  templates/transporte/
  tests/
  exceptions.py
  urls.py
agendamentos/
  models/
  forms/
  services/
  views/
  templates/agendamentos/
  tests/
  exceptions.py
  urls.py
equipamentos/
  models/
  forms/
  services/
  views/
  templates/equipamentos/
  tests/
  exceptions.py
  urls.py
templates/
  base.html
static/
  css/site.css
```

Cada pacote `models/`, `views/`, `services/` e `forms/` reexporta suas classes públicas no `__init__.py`.

## Layout base (`templates/base.html`)

Todas as páginas herdam deste template mobile-first, que contém:

- `<html lang="pt-br">` e a meta tag `viewport`
- Aplicação dinâmica de classes CSS no `<body>` conforme as preferências de acessibilidade motora do usuário autenticado (`toque-padrao`, `toque-expandido`, `toque-maximo` e `alto-contraste`), garantindo alvos de toque mínimos de 48x48 px (WCAG 2.1 AA)
- Cabeçalho com identificação do sistema **SemBarreiras — ADEFAL**, atalho rápido para o Botão de Pânico (quando autenticado como PCD) e navegação entre os módulos
- Para visitantes: links "Entrar" e "Cadastrar"
- Para usuários autenticados: indicação do perfil ativo (`PCD` ou `Cuidador`), link para "Acessibilidade" e botão "Sair" em formulário POST com `{% csrf_token %}`
- Área de mensagens do framework `django.contrib.messages`
- Blocos `title` e `content`

## URLs do projeto (`core/urls.py`)

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("contas.urls")),
    path("emergencia/", include("emergencia.urls")),
    path("transporte/", include("transporte.urls")),
    path("agendamentos/", include("agendamentos.urls")),
    path("equipamentos/", include("equipamentos.urls")),
]
```

## Teste de arquitetura

`contas/tests/test_arquitetura.py` percorre os módulos `views` de todos os 5 apps (`contas`, `emergencia`, `transporte`, `agendamentos`, `equipamentos`) e todas as rotas de `core.urls`, e falha se:

1. uma classe definida no módulo com nome terminado em `View` não tiver `django.views.View` diretamente em `__bases__`;
2. uma função pública for usada como view em `urls.py`, ou seja, algum padrão de URL não apontar para uma view criada com `as_view()` (com exceção das rotas do Admin).

## Testes

- [x] `python manage.py check` não reporta problemas.
- [x] `python manage.py migrate` executa usando `contas.Usuario` no PostgreSQL.
- [x] O teste automatizado de arquitetura passa para todos os apps.

