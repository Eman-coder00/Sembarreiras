# ADR 0001: MVT com camada de service e views baseadas em `View`

- **Status:** Aceito
- **Data:** 2026-11-10

## Contexto

No Django, a regra de negócio costuma se espalhar entre views, forms, models e signals. Em um sistema com regras críticas de segurança, saúde e mobilidade como o SemBarreiras (acionamento de emergência, vínculo de cuidador por OTP, antecedência de 24h/48h em agendamentos e validação de laudos), espalhar regras dificulta testá-las sem cliente HTTP e reutilizá-las entre as telas de usuário PCD, cuidador e Django Admin.

As generic views reduzem código, mas escondem o fluxo em herança e tendem a levar regra de negócio para métodos sobrescritos.

## Decisão

O projeto segue MVT, com todas as regras de negócio e consultas ao ORM concentradas em uma camada de service que não conhece HTTP. Toda view é uma classe que herda diretamente de `django.views.View`, sem views baseadas em função nem generic views.

As regras completas de cada camada estão em [`docs/arquitetura.md`](../arquitetura.md).

## Consequências

- As regras de negócio (como prazos de cancelamento, limite de contatos de emergência e permissões de cuidador) podem ser testadas diretamente nos services, sem cliente HTTP.
- O Django Admin e os diferentes perfis reaproveitam as mesmas regras chamando os services.
- Há mais código explícito nas views para lidar com formulários e conversão de exceções de domínio.
- O `ModelForm.save()` não é usado, pois toda gravação passa pelo service.
- Um teste automatizado de arquitetura verifica a herança de todas as views e rotas do projeto.

