# API Certify

Uma API moderna para autenticação e gerenciamento de usuários, construída com FastAPI seguindo os princípios de Layered Architecture e Repository Pattern.

## Arquitetura

O projeto segue uma arquitetura em camadas bem definida:

```
api_certify/
├── core/           # Lógica de negócio central
├── models/         # Modelos de dados e entidades
├── schemas/        # Esquemas Pydantic para validação
├── repositories/   # Camada de acesso a dados (Repository Pattern)
├── service/        # Camada de serviços
├── routes/         # Endpoints da API
├── dependencies.py # Injeção de dependências
├── exceptions/     # Tratamento de exceções
├── infra/          # Configurações de infraestrutura
└── main.py         # Ponto de entrada da aplicação
```

## Tecnologias

- **FastAPI** 0.104.1 - Framework web moderno
- **Python** 3.9+ - Linguagem de programação
- **MongoDB** - Banco de dados (via Motor/PyMongo)
- **Poetry** - Gerenciamento de dependências
- **Pydantic** 2.12.2 - Validação de dados
- **bcrypt** 4.1.2 - Criptografia de senhas
- **Ruff** - Linting e formatação
- **Pytest** - Framework de testes

## Instalação

### Pré-requisitos
- Python 3.9+
- Poetry
- MongoDB

### Configuração

1. Clone o repositório
```bash
git clone <repository-url>
cd api-certify
```

2. Instale as dependências
```bash
poetry install
```

3. Configure as variáveis de ambiente
```bash
cp .env.example .env
```

Variáveis necessárias:
```
DB_URL=mongodb+srv://project_name:<password>@cluster0.salfi3n.mongodb.net/?appName=Cluster0
DB_NAME=CERTIFY
```

4. Execute a aplicação
```bash
poetry run task run
```

## Comandos Úteis

### Desenvolvimento
```bash
poetry run task run          # Inicia servidor de desenvolvimento
poetry run task lint         # Executa linting
poetry run task format       # Formata código
poetry run task pre_format   # Correções automáticas do lint
```

### Testes
```bash
poetry run task test         # Executa testes com coverage
poetry run task pre_test     # Roda lint antes dos testes
```

## Testes

O projeto inclui uma suíte de testes completa:

```bash
# Executar todos os testes
pytest

# Com coverage report
pytest --cov=api_certify

# Testes específicos
pytest tests/ -v
```

## Estrutura de Desenvolvimento

### Padrões de Commit
Siga o padrão de commits semânticos:
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes

### Branches
- `feat/nome-da-feature`
- `fix/descricao-do-bug`
- `chore/ajuste-menor`

## Funcionalidades

- Autenticação de usuários
- Criptografia de senhas com bcrypt
- Validação de dados com Pydantic v2
- Repository Pattern para acesso a dados
- Injeção de dependências
- Tratamento centralizado de exceções
- Documentação automática da API (Swagger/OpenAPI)

## Documentação da API

Após iniciar o servidor, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## Contribuição

Consulte o CONTRIBUTING.md para diretrizes detalhadas de contribuição.

## Licença

Este projeto está sob a licença MIT.

---

**Desenvolvido por** Comunidade Frontend Fusion
