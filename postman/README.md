# Executar Certify no Postman

O Postman envia requisições; a API e o MongoDB precisam estar rodando.

## No aplicativo Postman

1. Clique em **Import** e selecione `Certify-Local.postman_collection.json` e `Certify-Local.postman_environment.json` desta pasta.
2. Selecione o ambiente **Certify Local**.
3. No ambiente, preencha `access_key_system` com o valor de `ACCESS_KEY` do arquivo `API_CERTIFY/.env`. Mantenha o segredo local, sem compartilhá-lo.
4. Abra a coleção **Certify - Teste local completo**, clique em **Run** e execute as 16 requisições em ordem, começando pela primeira.

O primeiro pedido gera e-mails e CNPJ de teste com dígitos verificadores. Os pedidos seguintes capturam IDs e tokens automaticamente. Cada execução cria duas contas, um evento e um certificado no banco local. Esses registros são mantidos para inspeção. Para usar as requisições isoladamente, execute antes suas dependências; para manter a sessão após o teste, não execute o último pedido de logout.

Use o aplicativo desktop ou o Desktop Agent para acessar `localhost` a partir da versão web do Postman.

## Pelo terminal

Na raiz `Certify`:

```powershell
& API_CERTIFY/.venv-local/Scripts/python.exe API_CERTIFY/postman/run_local.py
```

Esse comando lê a chave do `.env`, prepara um ambiente temporário, executa o Postman CLI e remove o arquivo temporário ao terminar. Não requer login para a execução local e usa `--no-report-events`.

Se a API estiver parada, em outro terminal:

```powershell
cd API_CERTIFY
$env:PYTHONUTF8 = '1'
& ./.venv-local/Scripts/python.exe -m uvicorn api_certify.main:app --host 127.0.0.1 --port 8000
```

O container MongoDB criado para este projeto pode ser iniciado, caso esteja parado, com:

```powershell
docker start certify-mongo-local
```

## Escopo

O fluxo cobre saúde, cadastro de participante/empresa, login, perfil, criação/consulta/edição de evento, emissão/consulta/listagem/validação pública de certificado, renovação de token e logout. Não cobre upload, recuperação de senha, emissão em lote e todos os cenários de erro. A coleção anterior `../postman_collection.json` foi preservada.

Para continuar a validação, ampliar a coleção com esses fluxos e cenários de autorização. A documentação interativa de todos os endpoints está em http://localhost:8000/docs.
