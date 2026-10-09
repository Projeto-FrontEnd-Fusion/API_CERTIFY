# Contrato de integração do aluno

Todas as rotas usam `/api/v1`. Rotas de perfil exigem `Authorization: Bearer <access_token>`.

- `GET /auth/me`: retorna `data.auth` com `_id`, `fullname`, `email`, `phone`, `cpf`, `birth_date` (DD/MM/AAAA) e `avatar_url`.
- `PUT /auth/{user_id}`: JSON com `fullname`, `email`, `phone`, `cpf` e `birth_date` opcionais. Só permite alterar o próprio usuário. Retorna `data.auth` atualizado.
- `POST /upload/avatar`: multipart com campo `file`, PNG/JPEG, até 5 MB. Persiste a URL no usuário e retorna `data.url`. A URL relativa é resolvida contra a origem do backend.
- `POST /auth/change-password`: JSON `current_password`, `new_password`. Confere a senha atual e aplica a regra de força existente. Retorna sucesso somente após persistir.
- Recuperação: `POST /auth/forgot-password` com `email`; `POST /auth/verify-code` com `email`, `code` (6 dígitos); `POST /auth/reset-password` com `email`, `code`, `new_password`.
- `GET /certificate/users/{user_id}` lista certificados em `data.items`; `GET /certificate/{certificate_id}` busca um certificado por seu próprio ID.
- `GET /certificate/validate/{access_key}` valida um certificado existente. O aluno não deve chamar a emissão restrita à empresa.

O frontend não simula sucesso de gravação. Erros da API são exibidos sem atualizar o estado salvo.
