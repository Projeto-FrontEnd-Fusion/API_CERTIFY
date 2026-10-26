# Notificações da empresa

Autenticação Bearer obrigatória. Apenas empresa/admin; o destinatário é sempre
o `sub` do JWT, nunca um ID informado pelo cliente. Sem avisos fictícios.

- `GET /api/v1/notifications?page=1&limit=5`: página (>=1), limite (1..100).
  Envelope `success`, `message`, `data`: `items`, `total`, `unread_count`,
  `page`, `total_pages`. Ordenação: avisos de falha não lidos primeiro,
  depois data decrescente e ID para desempate.
- Item: `id`, `type` (`certificate`), `severity` (`info`/`warning`), `title`,
  `description`, `created_at` (UTC ISO 8601), `read`, `href` (rota interna).
- `PATCH /api/v1/notifications/read-all`: marca os eventos atualmente existentes
  como lidos e devolve `data.updated`. Eventos posteriores continuam não lidos.
- `PATCH /api/v1/notifications/{id}/read`: idempotente; devolve o item atualizado
  em `data.notification`. IDs inexistentes ou de outra empresa retornam 404.
- Token inválido/ausente: 401/403 conforme middleware; aluno: 403;
  parâmetros inválidos: 422; indisponibilidade do Mongo: 503.

Fonte: certificados persistidos da empresa. Cada emissão gera um evento;
envio de e-mail aceito pelo SMTP gera outro; falha de envio gera um aviso
enquanto a falha estiver ativa. IDs estáveis por certificado e evento, incluindo
o número da tentativa para falhas. `sent` significa aceitação pelo SMTP,
não comprovação de entrega na caixa de entrada.

O feed contempla certificados existentes, sem migração ou duplicação dos dados.
A leitura é persistida na coleção `notification_reads`, com ID único por evento
e destinatário. Consultas filtram `issuer_id` antes de compor o feed. A listagem
não grava dados e não altera os estados de envio de e-mail.

Manutenção, instabilidade, alunos e modelos só devem aparecer quando existir
uma fonte real para esses eventos; não são inferidos nem simulados.
