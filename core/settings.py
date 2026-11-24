"""
Configurações Django para o projeto SemBarreiras (MobiLivre — ADEFAL).
"""

import os
from pathlib import Path

import dj_database_url
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

_ENV_PATH = BASE_DIR / ".env"
if _ENV_PATH.is_file():
    for _linha in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _linha = _linha.strip()
        if not _linha or _linha.startswith("#") or "=" not in _linha:
            continue
        _chave, _valor = _linha.split("=", 1)
        _chave = _chave.strip()
        _valor = _valor.strip().strip('"').strip("'")
        if _chave and _valor:
            os.environ.setdefault(_chave, _valor)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

# Sem a variável, o desenvolvimento usa uma chave temporária, e as sessões caem ao
# reiniciar o servidor. Fora dele, a chave fica vazia e o Django se recusa a usá-la.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or (
    get_random_secret_key() if DEBUG else ""
)

_allowed_hosts_env = os.environ.get("DJANGO_ALLOWED_HOSTS")
ALLOWED_HOSTS: list[str] = (
    [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()]
    if _allowed_hosts_env
    else ["localhost", "127.0.0.1", "testserver", ".onrender.com"]
)

_csrf_origins_env = os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS: list[str] = (
    [origin.strip() for origin in _csrf_origins_env.split(",") if origin.strip()]
    if _csrf_origins_env
    else ["https://*.onrender.com"]
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "contas",
    "emergencia",
    "transporte",
    "agendamentos",
    "equipamentos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"
ASGI_APPLICATION = "core.asgi.application"

# Banco de dados PostgreSQL conforme ADR 0003 (suporte a DATABASE_URL na nuvem e local via env)
if os.environ.get("DATABASE_URL"):
    DATABASES = {
        "default": dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "sem_barreiras"),
            "USER": os.environ.get("POSTGRES_USER", "postgres"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"

TIME_ZONE = "America/Maceio"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Diretório de uploads protegidos (sem rota estática pública — ADR 0005)
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/anexos-protegidos/"

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "contas.Usuario"

LOGIN_URL = "contas:entrar"

