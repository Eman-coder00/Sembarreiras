# ADR 0005: Armazenamento protegido e validação de anexos clínicos

- **Status:** Aceito
- **Data:** 2026-11-10

## Contexto

A solicitação de empréstimo de equipamentos de apoio exige o envio de laudo médico e comprovante de residência ([PRD 0001](../prd/0001-sem-barreiras.md)). Esses arquivos contêm dados pessoais sensíveis de saúde protegidos pela LGPD e representam vetor de risco caso arquivos executáveis ou maliciosos sejam enviados ou caso os documentos fiquem acessíveis por URLs públicas diretas.

## Decisão

- Aceitar apenas arquivos nos formatos PDF, JPEG e PNG, validando no Form e no Service tanto a extensão quanto a assinatura de bytes (magic bytes / cabeçalho do arquivo) e o limite de tamanho (10 MB para laudo médico e 5 MB para comprovante de residência).
- Salvar os arquivos fora do diretório `static/`, utilizando nomes gerados com identificadores aleatórios seguros (`uuid4`) e sem permissão de execução.
- Não expor o diretório de uploads diretamente em URLs públicas: o download ou visualização do anexo passa obrigatoriamente por uma `View` autenticada que consulta o `EquipamentoService` para verificar se o solicitante é o titular PCD, seu cuidador com vínculo ativo ou um membro autorizado da equipe da ADEFAL (`is_staff`).

## Consequências

- Laudos médicos e comprovantes não podem ser acessados por enumeração de URL nem por usuários não autorizados, e arquivos forjados com extensão trocada são rejeitados antes da gravação.
- Servir arquivos por meio de view autenticada adiciona sobrecarga ao processo Python em comparação a um servidor web estático, custo aceitável para o volume local do projeto em troca do controle estrito de acesso.

