**Título:** Correções no Schema de Certificados

**Principais melhorias/correções:**
• Corrigido o valor do enum `Status.AVALIABLE` de "avaliable" para "available" (correção de typo)
• Reestruturado completamente o modelo `CreateCertificate` para incluir campos obrigatórios: `fullname`, `email`, `access_key`, `event_id` e `status`
• Renomeado `CertificateResponse` para `CertificateInDb` para melhor refletir que representa o modelo completo do banco de dados
• Tornado `access_key` obrigatório no `CreateCertificate` (era opcional anteriormente)
• Adicionado campo `status` como obrigatório no `CreateCertificate`
• Incluído validação de email com `EmailStr` no `CreateCertificate`
• Mantida a estrutura completa do modelo de banco com todos os campos necessários para certificados



**Título:** Injeção de Dependência para CertificateService

**Principais melhorias/correções:**
• Adicionado `AuthRepository` como dependência no `get_certificate_service`
• Agora o `CertificateService` recebe tanto `certificate_repository` quanto `auth_repository` como parâmetros
• Reorganização da ordem das funções no arquivo para melhor estruturação
• Removido espaço em branco excessivo entre as funções
• Mantida a funcionalidade existente de todos os outros repositórios e serviços


**Título:** Adição de Método de Verificação de Usuário

**Principais melhorias/correções:**
• Adicionado novo método isExistAuth para verificar existência de usuário por ID
• Implementada conversão de string para ObjectId na busca por usuário
• Método retorna bool (True se usuário existe, False caso contrário)
• Mantida toda a funcionalidade existente de criação e login de usuários
• Adicionada importação do ObjectId do módulo bson
• Estrutura do repositório mantida inalterada para os métodos anteriores



**Título:** Validação de Usuário e Prevenção de Duplicatas no CertificateService

**Principais melhorias/correções:**
• Adicionado `AuthRepository` como dependência no construtor do serviço
• Implementada validação de existência do usuário usando `auth_repository.isExistAuth()`
• Adicionada verificação de certificado duplicado usando `find_existing_certificate`
• Substituído `CertificateResponse` por `CertificateInDb` em todos os tipos de retorno
• Implementada lógica de retorno do certificado existente caso já exista (evita duplicação)
• Melhorado tratamento de erros com mensagens mais específicas
• Mantida a compatibilidade com os métodos do repositório



**Título:** Refatoração do CertificateRepository e Prevenção de Duplicatas

**Principais melhorias/correções:**
• Substituído `CertificateResponse` por `CertificateInDb` em todos os retornos
• Criada função `find_existing_certificate` para verificar duplicatas (user_id + event_id)
• Implementada lógica de prevenção de certificados duplicados no método `create`
• Refatorada `mocked_certificate` para receber parâmetros dinâmicos (access_key, status)
• Removida verificação redundante de usuário no método `create`
• Simplificada a criação do certificado usando dados diretos do `certificate_data`
• Removida a geração manual de `certificate_dict` e atualizações complexas
• Mantida a funcionalidade de conversão de ObjectId para string
• Melhorada a documentação dos métodos com docstrings

