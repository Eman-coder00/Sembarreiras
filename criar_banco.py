"""Cria o banco de dados PostgreSQL definido no arquivo .env caso ainda não exista."""

import os
from pathlib import Path

import psycopg
from psycopg import sql

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.is_file():
    for linha in ENV_PATH.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        chave = chave.strip()
        valor = valor.strip().strip('"').strip("'")
        if chave and valor:
            os.environ.setdefault(chave, valor)


def salvar_senha_no_env(usuario_pg: str, nova_senha: str) -> None:
    conteudo = (
        "# Configurações locais do SemBarreiras (não vai para o Git)\n"
        "DJANGO_SECRET_KEY=\n\n"
        "# Configurações do PostgreSQL local:\n"
        f"POSTGRES_DB={os.environ.get('POSTGRES_DB', 'sem_barreiras')}\n"
        f"POSTGRES_USER={usuario_pg}\n"
        f"POSTGRES_PASSWORD={nova_senha}\n"
        f"POSTGRES_HOST={os.environ.get('POSTGRES_HOST', 'localhost')}\n"
        f"POSTGRES_PORT={os.environ.get('POSTGRES_PORT', '5432')}\n"
    )
    ENV_PATH.write_text(conteudo, encoding="utf-8")


def garantir_banco() -> None:
    nome_banco = os.environ.get("POSTGRES_DB", "sem_barreiras")
    usuario = os.environ.get("POSTGRES_USER", "postgres")
    senha = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    porta = os.environ.get("POSTGRES_PORT", "5432")

    while True:
        try:
            with psycopg.connect(
                dbname="postgres",
                user=usuario,
                password=senha,
                host=host,
                port=porta,
                autocommit=True,
            ) as conn:
                salvar_senha_no_env(usuario, senha)
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s",
                        (nome_banco,),
                    )
                    existe = cur.fetchone() is not None
                    if not existe:
                        cur.execute(
                            sql.SQL("CREATE DATABASE {}").format(
                                sql.Identifier(nome_banco)
                            )
                        )
                        print(
                            f"\nSucesso! Banco de dados '{nome_banco}' criado no PostgreSQL e senha salva em sistema/.env!"
                        )
                    else:
                        print(
                            f"\nSucesso! Banco de dados '{nome_banco}' já existe no PostgreSQL e senha salva em sistema/.env!"
                        )
                break
        except psycopg.OperationalError as exc:
            print(f"\nNão foi possível conectar com o usuário '{usuario}' e a senha atual.")
            print(f"Detalhe: {exc}")
            nova_senha = input(
                f"Digite a senha do usuário '{usuario}' do seu PostgreSQL (ou Ctrl+C para sair): "
            ).strip()
            if nova_senha:
                senha = nova_senha


if __name__ == "__main__":
    garantir_banco()
