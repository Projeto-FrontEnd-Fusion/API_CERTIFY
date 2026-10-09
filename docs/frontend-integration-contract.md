# Integração das telas de certificados e recuperação

Todas as rotas usam `/api/v1`. Login e cadastro mantêm seus contratos.

CORS padrão permite o desenvolvimento por `http://localhost:5173` e `http://127.0.0.1:5173`, inclusive preflight de POST com Content-Type e Authorization. `FRONTEND_URLS`, quando definido, substitui a lista padrão e deve incluir as origens necessárias.

- `GET /certificate/{id}`: certificado autenticado; somente participante, emissor ou administrador.
- `GET /certificate/validate/{access_key}`: público; dados de apresentação e validade, sem e-mail, usuário ou notificações. Certificados indisponíveis ou vencidos retornam 404. Mantém campos públicos existentes e adiciona instituição, descrição, código e validade.
- `POST /certificate/batch`: adiciona `notify_students` (padrão true). false grava notificações do aluno como deferred; empresa continua recebendo confirmação.
- `POST /certificate/send-links`: corpo `{certificate_ids: string[]}` (1 a 200 IDs únicos). Usuário só envia seus próprios certificados; empresa só os que emitiu. Processa exclusivamente os alunos selecionados e retorna `{sent, failed, pending, total}`. Um certificado já enviado não é reenviado. SMTP sem configuração retorna 503. Falhas de destinatário são persistidas e retornadas, sem sucesso fictício.
- `POST /auth/forgot-password`: mantém corpo e resposta; envia código via SMTP em vez de gravá-lo em log. Falha do transporte retorna 503.

Frontend busca certificados por ID na URL, valida com a chave original (sensível a maiúsculas), lista por emissor com paginação e gera PDF local a partir dos dados reais. Emissão cria evento e certificados em lote; preserva rascunho e ID do evento até a emissão completar para permitir nova tentativa sem criar outro evento. Modal acompanha a requisição e mostra contagens confirmadas, sem porcentagem de envio inventada.

Configuração: `VITE_API_URL` termina em `/api/v1`; SMTP usa as variáveis de `docs/certificate-email-contract.md`. Testes locais usam transporte substituído e não enviam mensagens externas.
