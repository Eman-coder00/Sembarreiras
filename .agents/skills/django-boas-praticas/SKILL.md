---
name: django-boas-praticas
description: Boas práticas de Django para este projeto. Use ao criar ou alterar models, migrações, services, views, forms, templates, URLs, Admin, configurações ou testes Django.
---

# Boas práticas de Django

O projeto usa Django 6.1. As regras de arquitetura estão em `docs/arquitetura.md` e prevalecem sobre esta skill. Em caso de dúvida sobre uma API, consulte a documentação da versão instalada.

## Views

- Herde diretamente de `View` e implemente apenas `get` e `post`, quando necessários.
- Mantenha cada método curto: ler a entrada, chamar o service e responder.
- Converta exceções de domínio em respostas HTTP, como `Http404`.
- Redirecione após um POST bem-sucedido para evitar reenvio ao recarregar a página.
- Use apenas POST para alterar dados, nunca GET.
- Use `LoginRequiredMixin` antes de `View` na lista de classes base.

```python
class PostCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "posts/form.html", {"form": PostForm()})

    def post(self, request):
        form = PostForm(request.POST)
        if not form.is_valid():
            return render(request, "posts/form.html", {"form": form})
        PostService.criar(autor=request.user, **form.cleaned_data)
        return redirect("posts:painel")
```

## Services

- Concentre aqui as regras de negócio e as consultas ao ORM.
- Receba dados simples ou objetos de domínio, nunca `request`.
- Levante exceções de domínio, sem `Http404` nem outros tipos HTTP.
- Use `transaction.atomic()` quando uma operação fizer mais de uma escrita dependente.
- Use `only()`, `values()` e agregações quando evitarem carregar dados desnecessários.

## Models e migrações

- Mantenha nos models apenas campos, relacionamentos, constraints, índices, `Meta` e `__str__`.
- Proteja invariantes no banco com `UniqueConstraint` e `CheckConstraint`.
- Referencie o usuário com `settings.AUTH_USER_MODEL` em models e com `get_user_model()` no restante do código.
- Escolha `on_delete` conscientemente. Use `PROTECT` quando a exclusão perderia dados importantes.
- Use `TextChoices` para valores fixos.
- Use `null=True` em campos de texto só quando houver motivo: normalmente basta `blank=True`.
- Gere migrações com `makemigrations`, revise o arquivo e versione-o. Não edite migrações já aplicadas em outros ambientes.
- Prefira não usar signals para regras de negócio, pois eles escondem o fluxo.

## Consultas

- Evite N+1: use `select_related` para ForeignKey e `prefetch_related` para relações múltiplas.
- Use `exists()` para verificar existência e `count()` para contar, em vez de carregar a lista.
- Use `F()` para atualizações baseadas no valor atual e `update()` ou `bulk_create()` para lotes.
- Pagine listagens públicas.
- Adicione índices com base nos filtros e ordenações realmente usados.

## Forms

- Use forms para validar toda entrada de usuário e leia os valores de `cleaned_data`.
- Declare os campos explicitamente em `Meta.fields`. Nunca use `"__all__"`.
- Deixe no form a validação de formato e no service as regras que dependem do estado do sistema.

## Templates e URLs

- Use herança com `{% extends %}` e reutilize trechos com `{% include %}`.
- Coloque templates de app em `<app>/templates/<app>/` para evitar conflito de nomes.
- Não coloque consultas nem regras de negócio nos templates.
- Nomeie as rotas e use `app_name`. Gere links com `{% url %}` e `reverse()`, sem caminhos fixos.
- Use `{% static %}` para arquivos estáticos.

## Segurança

- Inclua `{% csrf_token %}` em todo formulário POST.
- Não use `safe` nem `mark_safe` em conteúdo enviado por usuários.
- Valide redirecionamentos vindos do usuário com `url_has_allowed_host_and_scheme`.
- Verifique no service se o usuário tem direito ao objeto, e não apenas se está autenticado.
- Não use SQL com interpolação de texto. Prefira o ORM ou parâmetros em consultas brutas.
- Leia `SECRET_KEY` de variável de ambiente e use `DEBUG = False` fora do desenvolvimento.
- Rode `python manage.py check --deploy` antes de qualquer deploy.

## Admin

- Declare `list_display`, `list_filter` e `search_fields` quando forem úteis, e use `list_select_related` para evitar N+1.
- Faça as ações do Admin chamarem services, para não duplicar regras.
- Bloqueie a escrita em models cujas regras dependem de um service.

## Tempo e configuração

- Use `django.utils.timezone.now()`, nunca `datetime.now()`.
- Mantenha `USE_TZ = True`.
- Importe configurações com `from django.conf import settings`.

## Testes

- Use `django.test.TestCase` e crie dados compartilhados em `setUpTestData`.
- Teste as regras diretamente nos services e use `self.client` para rotas, permissões, status e redirecionamentos.
- Verifique os casos de visitante, dono e outro usuário nas rotas protegidas.
- Use `assertNumQueries` em listagens para detectar N+1.
- Use `reverse()` nos testes, em vez de caminhos fixos.
- Rode `python manage.py test` e `python manage.py makemigrations --check` antes de concluir.

## Antes de concluir

- [ ] A view não contém regra de negócio nem acesso ao ORM.
- [ ] O service não conhece HTTP.
- [ ] Toda alteração de dados usa POST e CSRF.
- [ ] Rotas protegidas verificam a autenticação e o dono do objeto.
- [ ] As migrações foram geradas e revisadas.
- [ ] `python manage.py check` e os testes passam.
