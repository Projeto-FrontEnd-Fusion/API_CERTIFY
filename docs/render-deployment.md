# CI/CD e publicação no Render

## Pipeline do backend

O workflow `.github/workflows/ci.yml` roda em PRs, na `main` e manualmente. Não precisa de segredos de produção.

- Poetry e lockfile validados; Python 3.11 e 3.12.
- Ruff verifica erros de correção (`E9,F`), incluindo nomes indefinidos, imports e funções duplicadas. As regras antigas de estilo/complexidade do `pyproject.toml` continuam disponíveis em `poetry run task lint`; não são apresentadas como aprovadas pelo CI enquanto o legado não for corrigido.
- Pytest com relatórios JUnit e cobertura XML; mínimo de 85% no escopo definido pelo `pyproject.toml` (repositórios e infraestrutura de banco excluídos).
- Um job inicia MongoDB descartável e a API real; Postman executa o fluxo HTTP da coleção local. Nenhum banco ou SMTP de produção é utilizado.
- O Postman roda sem login, com `--no-report-events`. A saída de terminal é salva em `artifacts/postman.log` com `tee` e `pipefail`, preservando falhas de assertions. A opção `--output` exige login no Postman e não é utilizada neste CI.
- O check final `Backend CI passed` falha se qualquer job obrigatório falhar, for cancelado ou ignorado.
- Dependabot abre atualizações semanais de Python e GitHub Actions.
- Auditoria das versões de runtime do lockfile com pip-audit, bloqueando vulnerabilidades conhecidas. O frontend também bloqueia alertas altos/críticos com npm audit.

No GitHub, habilite Actions nos forks e configure uma regra de proteção para `main`, exigindo PR e o check `Backend CI passed`. Não habilite bypass para o fluxo normal de entrega.

## Render

O `render.yaml` do backend define um Web Service Python com `autoDeployTrigger: checksPass`. Assim, merges na `main` só disparam deploy automático depois que os checks passarem. Vincule o repositório usando a integração GitHub do Render; serviço criado apenas pela URL pública não tem o mesmo fluxo automático.

O Blueprint padrão usa explicitamente `free` para evitar cobrança acidental. Ele serve para demonstração: sem disco persistente, uploads desaparecem em reinícios; o Render bloqueia SMTP nas portas 25/465/587 nesse plano. A publicação completa com as funcionalidades atuais requer escolher um plano pago e adicionar disco, ou adaptar armazenamento e e-mail para serviços externos. Não aplicar recursos pagos sem escolher o plano antes.

Para persistência em um plano pago, configure um disco com mount path `/var/data` e a variável `UPLOAD_DIR=/var/data/uploads`. O backend já usa essa variável tanto na escrita quanto na exposição dos arquivos. Confira custo, tamanho e plano no painel antes de criar o disco. Disco limita a aplicação a uma instância e envolve breve interrupção durante deploy.

Variáveis do backend no painel:

| Variável | Valor |
|---|---|
| `DB_URL` | URI do MongoDB remoto, fornecida de forma privada no Render |
| `DB_NAME` | `CERTIFY`, ou o banco escolhido para o ambiente |
| `SECRET_KEY` | Gerada pelo Blueprint na criação; preservar em redeploys |
| `ACCESS_KEY` | Chave de emissão configurada privadamente |
| `FRONTEND_URLS` | Origem HTTPS do frontend, sem `/` final; aceita lista separada por vírgulas |
| `FRONTEND_URL` | Mesma origem, usada nos links dos e-mails |
| `UPLOAD_DIR` | Diretório no disco persistente, quando contratado |
| `EMAIL_WORKER_ENABLED` | `true` para processar pendências a cada minuto enquanto a API está ativa |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_SECURITY` | Configuração do provedor SMTP no plano compatível |

Use MongoDB remoto, como uma instância já existente no Atlas. Render não oferece MongoDB gerenciado; não substituir a URI por localhost. Autorize os endereços de saída do serviço no provedor de banco, conforme a política do projeto.

`/health` informa que o processo atende. `/ready` verifica o MongoDB e responde 503 quando indisponível; é a rota usada pelo health check do Render.

## Ordem de ativação

1. Revisar as alterações locais, abrir PR e validar o CI; manter credenciais fora do Git.
2. Conectar os dois forks ao Render via GitHub e escolher o plano do backend.
3. Criar o backend a partir de seu Blueprint, informar MongoDB e URLs previstas do frontend. A primeira publicação de um serviço pode ocorrer na criação; use somente um commit previamente validado.
4. Criar o Static Site pelo Blueprint do frontend. Definir `VITE_API_URL=https://<backend>.onrender.com/api/v1` **antes** do build. É variável pública compilada no bundle, não segredo.
5. Ajustar `FRONTEND_URLS` e `FRONTEND_URL` para a URL efetivamente atribuída ao frontend; conferir nomes gerados pelo Render, sem supor disponibilidade global.
6. Validar `/ready`, CORS, login, perfil, fotos, certificados e notificações no ambiente publicado. Testar atualização direta de `/perfil` para conferir o rewrite da SPA.

Se os serviços já existirem, atualizar a configuração deles; não criar duplicatas. Para rollback, selecionar um deploy anterior no painel, conferir variáveis e suspender deploy automático se necessário para manter a versão revertida. Rollback de código não reverte documentos MongoDB nem arquivos.

## Credenciais e estado

Validação local em 08/10/2026: 145 testes aprovados, cobertura de 87,32% no escopo configurado, Ruff `E9,F` aprovado, lockfile válido e pip-audit sem vulnerabilidades conhecidas nas dependências de runtime. A execução local utilizou Python 3.14; a matriz 3.11/3.12 ainda precisa executar no GitHub. O job HTTP/Postman com MongoDB real foi preparado, mas não executado localmente porque o daemon Docker não está ativo. Não considerar o CI remoto aprovado antes da execução dos workflows.

GitHub Actions executa CI; Render executa CD. Não há deploy hook nem token Render nos workflows. Segredos de banco/SMTP ficam exclusivamente nas variáveis privadas do Render. O painel precisa estar autenticado ou a ferramenta precisa de uma conexão autorizada para criar os serviços; adicionar os arquivos não cria uma publicação.

Referências: [CI no Render](https://render.com/docs/deploys), [Blueprint](https://render.com/docs/blueprint-spec), [plano gratuito](https://render.com/docs/free), [discos](https://render.com/docs/disks).
