# ADR 0002: Modelo de usuário customizado, perfis de acesso e autenticação própria

- **Status:** Aceito
- **Data:** 2026-11-10

## Contexto

O SemBarreiras atende dois perfis principais na interface pública — Usuário PCD Física e Cuidador/Tutor Legal — além da equipe administrativa/clínica da ADEFAL no Admin ([PRD 0001](../prd/0001-sem-barreiras.md)). O acesso exige identificação por CPF ou e-mail, seleção explícita do perfil na entrada, bloqueio temporário após 5 falhas consecutivas de senha e inativação lógica com mascaramento de dados pessoais para conformidade com a LGPD.

Além disso, o `LoginView` nativo do Django é uma generic view, o que a [ADR 0001](0001-mvt-com-camada-de-service.md) não permite.

## Decisão

- Criar o app `contas`, com o modelo `Usuario` herdando de `AbstractUser`, acrescentando CPF único e imutável, telefone, papel principal (`PCD` ou `CUIDADOR`), status cadastral (`ATIVO`, `INATIVO`, `BLOQUEADO`) e controle de tentativas de login.
- Definir `AUTH_USER_MODEL = "contas.Usuario"` antes da primeira execução de `migrate`.
- Manter os dados específicos de deficiência, equipamentos e preferências de acessibilidade motora em um modelo `PerfilPCD` associado ao usuário, e a relação entre cuidador e titular PCD em `VinculoCuidador` (pendente até confirmação por código OTP de 6 dígitos).
- Implementar a validação de credenciais (por CPF ou e-mail), contagem de falhas e bloqueio temporário de 15 minutos no `AutenticacaoService`.
- Chamar `login()` e `logout()` na view (classes que herdam de `View`), pois alteram a sessão HTTP e exigem `request`, registrando na sessão o perfil ativo selecionado no login.

## Consequências

- Um mesmo modelo de autenticação atende titulares PCD, cuidadores e administradores da ADEFAL, permitindo auditar acessos e aplicar bloqueio por tentativas inválidas no service.
- O código referencia o usuário apenas por `settings.AUTH_USER_MODEL` ou `get_user_model()`.
- A validação segura do redirecionamento (`next`), a expiração customizada da sessão ("Manter conectado" ou timeout estendido de acessibilidade) e o controle de tentativas ficam sob responsabilidade do app `contas`.

