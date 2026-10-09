# E-mails de certificado — tarefas #290 e #294

Interpretação: aluno recebe aviso com link de validação e acesso ao portal; empresa emissora recebe confirmação da emissão por certificado. Não há PDF anexado: a geração atual do PDF acontece no frontend.

As rotas existentes `POST /api/v1/certificate/{user_id}` e `POST /api/v1/certificate/batch` mantêm os contratos de resposta. O emissor vem do token, nunca do corpo enviado pelo cliente.

O certificado e os estados de notificação são gravados no mesmo documento MongoDB. Após responder à emissão, o backend tenta enviar os e-mails por SMTP. Falhas no SMTP não desfazem a emissão: o envio fica pendente para nova tentativa. Cada destinatário tem estado independente; emitir novamente um certificado existente não cria outra notificação.

Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SECURITY` (`starttls`, `ssl` ou `none`) e `FRONTEND_URL` (origem HTTPS do frontend). Usuário/senha são opcionais para servidores de teste locais. Sem host, remetente ou URL do frontend, os envios permanecem pendentes.

Os links usam `/validar-certificado/{access_key}` e `/meus-certificados`, existentes no frontend. O e-mail da empresa é obtido do cadastro do emissor. Alunos sem conta também recebem o aviso e podem validar o certificado pelo link público.

Para processar pendências após reinício ou falha do SMTP, agende a cada minuto, na pasta do backend:

```sh
python -m api_certify.send_certificate_emails
```

Falhas são retentadas após 5 minutos. Um envio interrompido pode ser retomado após 5 minutos. SMTP oferece entrega ao menos uma vez: uma interrupção entre o aceite pelo servidor SMTP e o registro no banco pode provocar duplicação. `Message-ID` permanece estável entre tentativas. Estado `sent` significa aceito pelo SMTP, não confirmação de leitura ou entrega na caixa de entrada.

Não configurar credenciais reais em arquivos versionados. Testes usam transportes simulados e não enviam mensagens externas.
