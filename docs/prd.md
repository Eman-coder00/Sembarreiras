# PRD 0001: SemBarreiras (Plataforma de Mobilidade e Assistência ADEFAL)

- **Status:** Aceito
- **Data:** 2026-11-10
- **Especificações:** [fundação](../specs/0001-fundacao.md), [contas, vínculo e acessibilidade](../specs/0002-contas-vinculo-e-acessibilidade.md), [emergência e botão de pânico](../specs/0003-emergencia-botao-panico.md), [transporte urbano acessível](../specs/0004-transporte-urbano-acessivel.md), [agendamentos e transporte hospitalar](../specs/0005-agendamentos-e-transporte-hospitalar.md), [equipamentos e laudos](../specs/0006-equipamentos-e-laudos.md), [dados iniciais](../specs/0007-dados-iniciais.md)

## Objetivo

Oferecer uma aplicação voltada à autonomia, mobilidade urbana e assistência em saúde de Pessoas com Deficiência Física (PCD) atendidas pela ADEFAL (Associação dos Deficientes Físicos de Alagoas) e seus cuidadores, reunindo acionamento rápido de emergência, consulta de ônibus acessíveis, agendamento de consultas com transporte hospitalar adaptado e solicitação de empréstimo de equipamentos de apoio.

## Perfis de uso

| Perfil | Quem é | O que precisa fazer |
|---|---|---|
| Usuário PCD Física | Pessoa com deficiência física cadastrada na ADEFAL | Configurar acessibilidade motora, cadastrar contatos de emergência, acionar o botão de pânico, consultar ônibus acessíveis, agendar consultas e transporte adaptado e solicitar empréstimo de equipamentos |
| Cuidador / Tutor Legal | Familiar, tutor ou profissional vinculado a um titular PCD | Acompanhar o histórico de emergências do titular vinculado, agendar ou remarcar consultas, solicitar transporte hospitalar e acompanhar pedidos de equipamentos em nome do titular |
| Equipe ADEFAL / Administrador | Profissional ou administrador institucional (`is_staff`) | Gerenciar vagas de consultas e frota adaptada, validar comprovantes na recepção, analisar laudos médicos e aprovar ou indeferir empréstimos de equipamentos |

## Requisitos funcionais

### Contas, Perfis e Acessibilidade

- **RF-01:** O usuário PCD realiza seu cadastro informando CPF válido e único, nome completo, data de nascimento, telefone/WhatsApp, e-mail único, senha (mínimo de 8 caracteres com letras e números), tipo de deficiência física, equipamentos de apoio utilizados e endereço residencial completo (com autopreenchimento por CEP ou preenchimento manual caso o CEP não seja localizado).
- **RF-02:** O titular PCD edita seus dados de contato, endereço e equipamentos de apoio mantendo o CPF imutável; alterações em telefone ou endereço exigem confirmação da senha atual e ficam registradas no histórico de auditoria, e a desativação da conta realiza inativação lógica com mascaramento de dados pessoais.
- **RF-03:** O usuário ou cuidador entra no sistema selecionando obrigatoriamente o perfil de acesso (Usuário PCD Física ou Cuidador/Tutor Legal) e informando CPF ou e-mail e senha, com opção de manter conectado; após 5 tentativas incorretas consecutivas, a conta fica temporariamente bloqueada por 15 minutos.
- **RF-04:** O cuidador realiza seu cadastro e solicita vínculo a um titular PCD ativo informando o CPF do titular; o vínculo nasce pendente e só é ativado após a confirmação de um código de validação de 6 caracteres enviado ao titular, podendo ser revogado a qualquer momento por qualquer uma das partes.
- **RF-05:** O usuário autenticado personaliza suas preferências de acessibilidade motora — tipo de limitação motora, equipamentos utilizados, tamanho dos componentes/áreas de toque (padrão, expandido ou máximo), tempo de expiração de tela (padrão ou prolongado de até 10 minutos) e modo de alto contraste — com aplicação imediata na interface.
- **RF-06:** O usuário ou cuidador recupera sua senha informando CPF ou e-mail e validando um código temporário de 6 dígitos com expiração de 15 minutos, definindo uma nova senha e invalidando sessões anteriores.

### Emergência e Botão de Pânico

- **RF-07:** O usuário PCD cadastra, edita e ordena até 3 contatos de emergência prioritários (1ª, 2ª e 3ª prioridade) com nome, telefone com DDD válido e grau de parentesco, sendo obrigatório manter ao menos 1 contato ativo na conta.
- **RF-08:** O usuário PCD aciona o botão de pânico, o que inicia uma janela de contagem regressiva de 5 segundos na tela antes do envio de qualquer alerta externo.
- **RF-09:** Durante os 5 segundos da contagem regressiva, o usuário pode cancelar o alerta imediatamente, abortando o envio de mensagens externas e registrando apenas o cancelamento no log interno de auditoria.
- **RF-10:** Caso a contagem regressiva termine sem cancelamento, o sistema captura as coordenadas geográficas atuais (ou a última localização conhecida) e dispara o alerta de emergência com link de localização para os contatos prioritários ativos, alternando automaticamente para envio via SMS caso o canal de dados falhe.
- **RF-11:** O usuário PCD e seus cuidadores vinculados consultam o histórico imutável de ocorrências de pânico, com filtro por intervalo de datas e status de envio, exibindo data, hora, coordenadas, endereço aproximado e contatos notificados.

### Transporte Urbano Acessível

- **RF-12:** O usuário consulta linhas de ônibus a partir de sua localização ou endereço de origem, número da linha ou destino e raio de busca, visualizando exclusivamente veículos que possuam acessibilidade física ativa (elevador ou rampa funcional).
- **RF-13:** Ao selecionar um veículo acessível da listagem, o usuário acompanha sua posição geográfica atualizada e a distância em metros até o ponto de parada selecionado.
- **RF-14:** O sistema calcula e exibe em destaque o tempo estimado de chegada (ETA) em minutos do próximo ônibus adaptado até o ponto de parada do usuário com base na distância restante e na velocidade média da via.

### Consultas e Transporte Hospitalar ADEFAL

- **RF-15:** O usuário PCD ou seu cuidador vinculado agenda consultas médicas e sessões de reabilitação na ADEFAL escolhendo especialidade, unidade de atendimento, profissional (opcional), data e horário disponível na grade, recebendo um número de protocolo único (`CNS-AAAAMMDD-XXXX`) sem permitir conflito de horários.
- **RF-16:** O usuário PCD ou seu cuidador vinculado cancela ou remarca uma consulta confirmada desde que a solicitação ocorra com antecedência mínima de 24 horas do horário agendado, liberando a vaga na grade e cancelando ou ajustando automaticamente o transporte hospitalar vinculado.
- **RF-17:** Para uma consulta ativa e confirmada, o usuário PCD ou cuidador solicita transporte hospitalar adaptado (van com plataforma elevatória) com antecedência mínima de 48 horas, informando endereço de embarque, necessidade de acompanhante e equipamento utilizado, desde que haja vaga disponível na frota para a região e horário.
- **RF-18:** Para toda consulta e/ou transporte hospitalar confirmado, o sistema emite um comprovante digital contendo os dados do agendamento e um QR Code assinado digitalmente, que pode ser visualizado em tela, baixado para impressão/PDF e validado pela recepção da ADEFAL para impedir adulterações.

### Empréstimo de Equipamentos de Apoio

- **RF-19:** O usuário PCD ou seu cuidador vinculado solicita empréstimo, doação ou manutenção de equipamento de apoio junto ao acervo da ADEFAL informando o tipo de equipamento, medidas corporais (largura do quadril, altura e peso), observações clínicas e anexando obrigatoriamente laudo médico e comprovante de residência, recebendo um número de protocolo único.
- **RF-20:** O sistema valida o upload do laudo médico (PDF, JPG ou PNG de até 10 MB) e do comprovante de residência (PDF, JPG ou PNG de até 5 MB), rejeitando formatos ou cabeçalhos inválidos e restringindo o acesso aos arquivos apenas ao titular, seu cuidador vinculado e à equipe autorizada da ADEFAL.
- **RF-21:** O usuário PCD e seu cuidador vinculado acompanham a linha do tempo da solicitação de equipamento pelo protocolo ou CPF (Em Análise Técnica, Aguardando Estoque, Aprovado / Pronto para Retirada, Deferido ou Indeferido), visualizando o parecer da equipe e as orientações de retirada.
- **RF-22:** Para equipamentos entregues em empréstimo temporário, o sistema exibe alertas de vencimento quando faltarem 7 dias e 2 dias para o fim do prazo e permite ao usuário solicitar renovação mediante justificativa ou confirmar a data de devolução para vistoria no almoxarifado.

## Requisitos não funcionais

- **RNF-01 (arquitetura):** O código segue as regras de [`docs/arquitetura.md`](../arquitetura.md) e a [ADR 0001](../adr/0001-mvt-com-camada-de-service.md).
- **RNF-02 (acessibilidade motora — WCAG 2.1 AA):** A interface oferece alvos de toque mínimos de 48x48 px (expansíveis nas preferências), modo de alto contraste, suporte a timeout de sessão prolongado de até 10 minutos e exigência de confirmação contra toques acidentais no botão de pânico.
- **RNF-03 (segurança e controle de acesso):** Toda alteração de dados utiliza POST com proteção CSRF, o conteúdo enviado por usuários é sempre escapado na exibição, senhas usam hash seguro do Django e toda operação verifica no service se o solicitante é o titular PCD ou cuidador com vínculo ativo.
- **RNF-04 (proteção de dados e LGPD):** Dados sensíveis de saúde e anexos clínicos têm acesso restrito a usuários autorizados ([ADR 0005](../adr/0005-armazenamento-e-validacao-de-anexos.md)), o CPF é imutável após o cadastro e a desativação da conta aplica inativação lógica com mascaramento dos dados identificáveis ([ADR 0003](../adr/0003-postgresql-como-banco-de-dados.md)).
- **RNF-05 (resiliência e operação local):** Os contatos de emergência e comprovantes confirmados ficam disponíveis em cache no navegador do dispositivo, e todas as integrações externas operam por simulação local determinística sem depender de serviços pagos ([ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)).
- **RNF-06 (qualidade e testes):** Cada requisito funcional possui pelo menos um teste automatizado cobrindo o fluxo principal e os caminhos de erro/permissão, e `python manage.py test` passa integralmente.

## Fora do escopo desta versão

- Aplicativos nativos compilados para Android/iOS em Flutter ou React Native (a entrega desta versão ocorre como aplicação web responsiva mobile-first renderizada no servidor).
- Suporte específico para deficiências visuais (leitores de tela avançados) ou intelectuais e navegação por comandos complexos de voz.
- Integração com gateways comerciais reais de SMS/WhatsApp, APIs proprietárias de GPS/mapas pagos ou sistemas legados externos da prefeitura e da ADEFAL ([ADR 0004](../adr/0004-simulacao-local-de-integracoes-externas.md)).
- Deploy produtivo em nuvem e infraestrutura de alta disponibilidade 24/7.

## Critérios de conclusão

1. Um usuário PCD consegue se cadastrar, personalizar a acessibilidade motora (alto contraste e áreas de toque expandidas), cadastrar contatos de emergência e executar tanto o cancelamento quanto o disparo completo do botão de pânico.
2. Um cuidador consegue solicitar vínculo a um titular PCD, ativá-lo mediante código OTP e atuar em nome do titular nos módulos permitidos, deixando de ter acesso imediatamente após a revogação do vínculo.
3. O usuário consegue consultar linhas de ônibus acessíveis, visualizar a posição e o ETA de um veículo adaptado, agendar uma consulta na ADEFAL com transporte hospitalar adaptado (respeitando as janelas de 24h e 48h) e emitir/validar o comprovante digital com QR Code assinado.
4. O usuário consegue submeter uma solicitação de equipamento de apoio com upload validado de laudo médico, acompanhar a mudança de status pela triagem da ADEFAL e solicitar renovação ou devolução de empréstimo.
5. Todos os requisitos funcionais possuem testes automatizados passando em `python manage.py test`, incluindo o teste automatizado de arquitetura.

