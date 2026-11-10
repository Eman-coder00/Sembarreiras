---
name: seguranca-owasp
description: Segurança de aplicações com base no OWASP Top 10:2025, aplicada a este projeto Django. Use ao criar ou revisar rotas, permissões, autenticação, formulários, consultas, tratamento de erros, configurações ou dependências, e ao fazer revisões de segurança.
---

# Segurança com o OWASP Top 10:2025

Referência: <https://top10.owasp.org/2025/>. Quando houver conflito, `docs/arquitetura.md` prevalece sobre esta skill. Esta lista é um ponto de partida para revisão, não uma garantia de que a aplicação está segura.

## A01: Controle de acesso quebrado

- Verifique no service se o usuário tem direito ao objeto, e não apenas se está autenticado.
- Filtre pelo dono na própria consulta, como em `PostService.obter_do_autor`, e responda 404 para que ninguém descubra se o objeto de outra pessoa existe.
- Altere dados apenas com POST e `{% csrf_token %}`. Não use `csrf_exempt`.
- Valide redirecionamentos vindos do usuário com `url_has_allowed_host_and_scheme`.
- Declare os campos em `Meta.fields`, para que um formulário não permita alterar `status`, `autor` ou `aprovado`.
- Teste as rotas protegidas com visitante, dono e outro usuário.

## A02: Configuração insegura

- Leia segredos de variáveis de ambiente, como `DJANGO_SECRET_KEY`. Nunca os coloque no código nem no Git.
- Fora do desenvolvimento, use `DEBUG = False`, preencha `ALLOWED_HOSTS` e ative cookies seguros, HTTPS e HSTS.
- Rode `python manage.py check --deploy` antes de qualquer deploy.
- Mantenha os middlewares de segurança, CSRF e clickjacking.

## A03: Falhas na cadeia de suprimentos de software

- Adicione uma dependência só quando for necessária e confira nome, origem e manutenção do pacote.
- Fixe as versões em um arquivo versionado e procure vulnerabilidades conhecidas, por exemplo com `pip-audit`.
- Não execute scripts baixados sem antes ler o que fazem.

## A04: Falhas criptográficas

- Use o sistema de senhas do Django (`create_user`, `set_password`). Não armazene nem compare senhas por conta própria.
- Use `secrets` ou `django.utils.crypto` para gerar valores secretos, nunca `random`.
- Não crie algoritmos próprios de criptografia nem de assinatura.

## A05: Injeção

- Prefira o ORM. Em SQL bruto, passe valores como parâmetros, sem interpolar texto.
- Mantenha o autoescape. Não use `safe`, `mark_safe` nem `autoescape off` em conteúdo enviado por usuários ([ADR 0003](../../../docs/adr/0003-conteudo-em-texto-puro.md)).
- Não use `eval`, `exec`, `pickle` nem `shell=True` com dados externos.
- Teste a exibição de conteúdo com `<script>`.

## A06: Design inseguro

- Identifique abusos possíveis ainda na spec: quem pode fazer o quê, com que limite e o que acontece em caso de erro.
- Proteja invariantes no banco com constraints, além das validações no código.
- Registre na spec e no PRD os riscos aceitos.

## A07: Falhas de autenticação

- Use `AuthenticationForm`, `login()`, `logout()` e os validadores de senha do Django.
- Não revele nas mensagens de erro se um usuário existe.
- Encerre a sessão apenas com POST.
- Trate a falta de limite de tentativas de login como risco a resolver antes de um deploy real.

## A08: Falhas de integridade de software ou dados

- Não desserialize dados não confiáveis com `pickle`.
- Grave pelos services, para que nenhum caminho ignore as regras. Por isso, o Admin bloqueia a escrita em `Post`.
- Não carregue scripts de CDN sem necessidade. Se precisar, use `integrity` (SRI).

## A09: Falhas de registro e alerta de segurança

- Registre eventos relevantes, como falhas de login e negações de acesso, sem depender de `print`.
- Não registre senhas, tokens, chaves de sessão nem dados pessoais desnecessários.
- Neutralize quebras de linha em valores enviados por usuários antes de registrá-los.

## A10: Tratamento incorreto de condições excepcionais

- Capture a exceção mais específica. Não silencie erros com `except:` vazio nem com `pass`.
- Falhe de forma segura: em caso de erro, negue o acesso e não deixe a operação pela metade. Use `transaction.atomic()` em escritas dependentes.
- Não mostre rastreamentos nem detalhes internos a visitantes. Converta exceções de domínio em respostas HTTP na view.
- Teste entradas inválidas, valores nos limites e recursos inexistentes.

## Ao revisar

Para cada problema, informe a categoria, o arquivo e a linha, o cenário de exploração e a correção. Não relate riscos hipotéticos como se fossem falhas confirmadas.
