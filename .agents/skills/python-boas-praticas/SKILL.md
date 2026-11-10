---
name: python-boas-praticas
description: Boas práticas de Python para este projeto. Use ao escrever, revisar ou refatorar qualquer código Python, incluindo nomes, tipagem, tratamento de exceções, organização de módulos e testes.
---

# Boas práticas de Python

O projeto usa Python 3.12. Quando houver conflito, `docs/arquitetura.md` prevalece sobre esta skill.

## Estilo e nomes

- Siga a PEP 8: 4 espaços, `snake_case` para funções e variáveis, `PascalCase` para classes e `UPPER_CASE` para constantes.
- Use termos do domínio em português e sufixos técnicos em inglês: `PostService.listar_publicados`, `ComentarioForm`, `PostListView`.
- Prefira nomes que dispensem comentários. Comente o motivo de uma decisão, não o que o código faz.
- Agrupe os imports em biblioteca padrão, terceiros e projeto. Não use `import *`.
- Use f-strings para formatar texto e `pathlib.Path` para caminhos.

## Funções e classes

- Dê uma única responsabilidade a cada função.
- Use retorno antecipado para evitar aninhamento profundo.
- Não use objetos mutáveis como valor padrão: troque `def f(itens=[])` por `def f(itens=None)`.
- Em funções com vários parâmetros do mesmo tipo, use argumentos nomeados para evitar trocas.
- Use `@staticmethod` ou `@classmethod` só quando a classe realmente agrupar o comportamento.
- Prefira composição a heranças profundas.

## Tipagem

- Anote assinaturas públicas, especialmente nos services.
- Use a sintaxe atual: `list[str]`, `dict[str, int]` e `str | None`, em vez de `List`, `Dict` e `Optional`.
- Use `TYPE_CHECKING` quando um import servir apenas para tipagem e criar dependência circular.

```python
def buscar_titulo(post_id: int) -> str | None:
    ...
```

## Exceções

- Capture a exceção mais específica possível. Nunca use `except:` vazio nem silencie erros com `pass`.
- Crie exceções de domínio para falhas previstas, como `PostNaoEncontrado`.
- Preserve a causa ao converter uma exceção: `raise Http404 from exc`.
- Mantenha o bloco `try` restrito às linhas que podem falhar.

## Coleções e recursos

- Use compreensões simples. Se ficarem difíceis de ler, use um `for`.
- Use `any()` e `all()` para verificações sobre coleções.
- Use `with` para arquivos, conexões e outros recursos.
- Use `datetime` com fuso horário. Em código Django, use `django.utils.timezone.now()`.

## Segurança

- Não coloque segredos no código. Leia-os de variáveis de ambiente.
- Não use `eval`, `exec` ou `pickle` com dados externos.
- Não registre senhas, tokens ou dados pessoais em logs.

## Testes

- Escreva testes com nomes que descrevam o comportamento: `test_publicar_preenche_data_na_primeira_vez`.
- Organize cada teste em preparar, executar e verificar, testando um comportamento por vez.
- Teste também caminhos de erro e casos de borda.
- Ao corrigir um bug, primeiro escreva um teste que o reproduza.

## Antes de concluir

- [ ] Os testes passam.
- [ ] Não há imports, variáveis ou código sem uso.
- [ ] As funções públicas novas têm tipos.
- [ ] Nenhum `except` esconde erros inesperados.
