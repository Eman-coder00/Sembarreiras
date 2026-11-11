#!/usr/bin/env python
"""Utilitário de linha de comando do Django para tarefas administrativas."""
import os
import sys
from pathlib import Path


def main() -> None:
    """Executa tarefas administrativas."""
    caminho_manage = Path(__file__).resolve()
    sys.argv[0] = str(caminho_manage)
    os.chdir(caminho_manage.parent)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Verifique se ele está instalado "
            "e se o ambiente virtual está ativo."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

