# Endpoints da API Certify — Guia para Postman

**Base URL:** `http://localhost:8000/api/v1`

---

## Rotas Públicas (sem token)

### 1. Health Check

```
GET http://localhost:8000/health
```

**Body:** nenhum

**Resposta esperada:**
```json
{
  "message": "API Certify está rodando!"
}
```

---

### 2. Cadastro de Usuário

```
POST /auth/signup
```

**Body:**
```json
{
  "fullname": "João Silva Santos",
  "email": "joao@email.com",
  "password": "SenhaSegura123!",
  "role": "user"
}
```

**Resposta esperada (201):**
```json
{
  "success": true,
  "message": "Usuário cadastrado com sucesso",
  "data": {
    "auth": {
      "_id": "...",
      "fullname": "João Silva Santos",
      "email": "joao@email.com",
      "role": "user",
      "status": "pending"
    }
  }
}
```

---

### 3. Login

```
POST /auth/login
```

**Body:**
```json
{
  "email": "joao@email.com",
  "password": "SenhaSegura123!"
}
```

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Sucesso no Login",
  "data": {
    "auth": {
      "_id": "...",
      "fullname": "João Silva Santos",
      "email": "joao@email.com",
      "role": "user",
      "status": "pending"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

> ⚠️ Copiar o `access_token` para usar nas rotas protegidas
> ⚠️ Copiar o `refresh_token` para renovação de tokens

---

### 4. Renovar Token (Refresh)

```
POST /auth/refresh
```

**Body:**
```json
{
  "refresh_token": "<refresh_token_do_login>"
}
```

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Token renovado com sucesso",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

> ⚠️ O refresh_token antigo é invalidado (rotação). Use o novo.

---

### 5. Logout

```
POST /auth/logout
```

**Header:** `Authorization: Bearer <access_token>`

**Body:**
```json
{
  "refresh_token": "<refresh_token_atual>"
}
```

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Sessão encerrada com sucesso"
}
```

---

### 4. Validar Certificado (pública)

```
GET /certificate/validate/{access_key}
```

**Body:** nenhum

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Certificado válido.",
  "data": {
    "certificate": {
      "participant_name": "João Silva Santos",
      "event_name": "Imersão Dev Insights",
      "workload": "9",
      "issued_at": "2025-01-15T00:00:00",
      "event_start": "2025-11-05T00:00:00",
      "event_end": "2025-11-07T00:00:00"
    }
  }
}
```

**Erro (404):**
```json
{
  "success": false,
  "message": "Certificado não encontrado"
}
```

---

### 5. Buscar Evento por ID (pública)

```
GET /events/{event_id}
```

**Body:** nenhum

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Evento obtido com sucesso.",
  "data": {
    "event": {
      "_id": "...",
      "name": "Imersão Dev Insights",
      "institution": "Comunidade Frontend Fusion",
      "workload": 9,
      "description": "Evento de tecnologia",
      "start_date": "2025-11-05T00:00:00",
      "end_date": "2025-11-07T00:00:00"
    }
  }
}
```

---

## Rotas Protegidas (requer token)

**Header obrigatório em todas as rotas abaixo:**

```
Authorization: Bearer <access_token_do_login>
```

---

### 6. Atualizar Dados do Usuário

```
PUT /auth/{user_id}
```

**Body (todos os campos são opcionais):**
```json
{
  "fullname": "João Atualizado",
  "email": "novoemail@email.com",
  "phone": "(85) 99124-8874"
}
```

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Dados atualizados com sucesso",
  "data": {
    "auth": {
      "_id": "...",
      "fullname": "João Atualizado",
      "email": "novoemail@email.com",
      "role": "user",
      "status": "pending"
    }
  }
}
```

**Erros possíveis:**
- 403 — Tentando atualizar perfil de outro usuário
- 404 — user_id não encontrado
- 409 — Email já cadastrado por outro usuário

---

### 7. Criar Evento

```
POST /events
```

**Body:**
```json
{
  "name": "Imersão Dev Insights",
  "institution": "Comunidade Frontend Fusion",
  "workload": 9,
  "description": "Evento voltado ao aprendizado e desenvolvimento em tecnologia.",
  "start_date": "2025-11-05T00:00:00",
  "end_date": "2025-11-07T00:00:00"
}
```

**Resposta esperada (201):**
```json
{
  "success": true,
  "message": "Evento criado com sucesso.",
  "data": {
    "event": {
      "_id": "...",
      "name": "Imersão Dev Insights",
      "institution": "Comunidade Frontend Fusion",
      "workload": 9,
      "description": "Evento voltado ao aprendizado e desenvolvimento em tecnologia.",
      "start_date": "2025-11-05T00:00:00",
      "end_date": "2025-11-07T00:00:00"
    }
  }
}
```

**Validações (422):**
- Nome com menos de 5 caracteres
- Carga horária ≤ 0
- Data de término anterior à data de início

---

### 8. Criar Certificado

```
POST /certificate/{user_id}
```

**Body:**
```json
{
  "fullname": "João Silva Santos",
  "email": "joao@email.com",
  "access_key": "<ACCESS_KEY_DO_ENV>",
  "event_id": "id_do_evento_criado",
  "status": "pending"
}
```

> ⚠️ O `access_key` é a chave do sistema (variável `ACCESS_KEY` do `.env`)
> ⚠️ O `event_id` deve ser um ID válido retornado ao criar evento

**Resposta esperada (201):**
```json
{
  "success": true,
  "message": "Certificado criado com sucesso.",
  "data": {
    "certificate": {
      "_id": "...",
      "user_id": "...",
      "access_key": "uuid-gerado-automaticamente",
      "status": "available",
      "participant_name": "João Silva Santos",
      "participant_email": "joao@email.com",
      "institution_name": "Comunidade Frontend Fusion",
      "event_id": "...",
      "event_name": "Imersão Dev Insights",
      "workload": "9",
      "issued_at": "2025-...",
      "valid_until": "2027-..."
    }
  }
}
```

**Erros possíveis:**
- 404 — Usuário não existe
- 404 — Evento não encontrado
- 400 — Chave de acesso inválida

---

### 9. Listar Certificados do Usuário

```
GET /certificate/users/{user_id}
```

**Body:** nenhum

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Certificados obtidos com sucesso.",
  "data": {
    "certificates": [
      {
        "_id": "...",
        "user_id": "...",
        "participant_name": "João Silva Santos",
        "event_name": "Imersão Dev Insights",
        "status": "available",
        "issued_at": "2025-..."
      }
    ]
  }
}
```

---

### 10. Buscar Certificado por ID

```
GET /certificate/{certificate_id}
```

**Body:** nenhum

**Resposta esperada (200):**
```json
{
  "success": true,
  "message": "Certificado obtido com sucesso.",
  "data": {
    "certificate": {
      "_id": "...",
      "user_id": "...",
      "participant_name": "João Silva Santos",
      "event_name": "Imersão Dev Insights",
      "status": "available"
    }
  }
}
```

---

## 🧪 Fluxo de Teste Completo

1. `POST /auth/signup` → criar conta
2. `POST /auth/login` → copiar `access_token` e `_id` do usuário
3. Configurar header `Authorization: Bearer <token>`
4. `POST /events` → criar evento, copiar `_id` do evento
5. `POST /certificate/{user_id}` → criar certificado usando o `event_id`
6. `GET /certificate/users/{user_id}` → listar certificados
7. `GET /certificate/validate/{access_key}` → validar com a chave pública do certificado (UUID retornado no passo 5)
8. `PUT /auth/{user_id}` → atualizar dados do perfil

---

## ⚙️ Configuração do Postman

### Variáveis de ambiente sugeridas:

| Variável | Valor |
|----------|-------|
| `base_url` | `http://localhost:8000/api/v1` |
| `token` | (preencher após login) |
| `user_id` | (preencher após signup/login) |
| `event_id` | (preencher após criar evento) |
| `access_key_system` | `<sua_access_key_do_env>` |

### Header padrão para rotas protegidas:

```
Authorization: Bearer {{token}}
```
