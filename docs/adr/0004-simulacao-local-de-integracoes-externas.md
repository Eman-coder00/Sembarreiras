# ADR 0004: Simulação local de integrações externas e recursos móveis

- **Status:** Aceito
- **Data:** 2026-11-10

## Contexto

O domínio do SemBarreiras envolve recursos de dispositivos móveis e serviços de terceiros: envio de alertas e tokens OTP por SMS/WhatsApp, consulta de CEP, telemetria em tempo real da frota de ônibus acessíveis, captura de GPS com resiliência offline e geração de comprovantes digitais com QR Code assinado ([PRD 0001](../prd/0001-sem-barreiras.md)). Depender de gateways pagos, chaves de API externas ou hardware específico inviabilizaria a execução determinística da suíte de testes automatizados (`python manage.py test`) e a avaliação offline do projeto.

## Decisão

- **Interface mobile-first no navegador:** construir a interface com templates Django responsivos e acessíveis (WCAG 2.1 AA), utilizando `localStorage` no navegador para cache offline de contatos de emergência e comprovantes, e a API de Geolocalização do navegador com opção de preenchimento/simulação de coordenadas para testes.
- **Mensageria (SMS, WhatsApp e E-mail):** encapsular os disparos em um service de notificações que registra cada mensagem enviada (destinatário, canal, conteúdo e status de entrega/fallback SMS) em banco de dados para consulta na interface e auditoria, usando o backend de e-mail em memória/console do Django.
- **Frota de ônibus e CEP:** manter as linhas, pontos de parada, veículos adaptados com status de elevador/rampa e base de CEPs em modelos locais populados por comando de carga inicial, permitindo simular o deslocamento e o cálculo de ETA de forma determinística.
- **QR Code e comprovante digital:** gerar a assinatura digital do comprovante com `hmac` (SHA-256) da biblioteca padrão do Python combinando protocolo, CPF, timestamp e `SECRET_KEY`, renderizando o QR Code em SVG e a versão para impressão/PDF sem exigir serviços externos.

## Consequências

- O sistema funciona 100% offline e sem custos ou cadastros em APIs de terceiros, e todos os fluxos (pânico, OTP, ônibus, ETA e validação de QR Code na portaria da ADEFAL) podem ser exercitados por testes automatizados rápidos e determinísticos.
- Não há envio real para a rede telefônica celular nem leitura de sensores físicos nativos de Android/iOS fora do navegador; a substituição por provedores reais no futuro fica isolada nos services de integração.

