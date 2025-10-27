# Guia de Contribuição

Obrigado por contribuir com este projeto!
Siga as orientações abaixo para mantermos o código organizado, padronizado e fácil de evoluir.

---

## Fluxo de Trabalho (GitHub Flow)

Este projeto segue o fluxo **GitHub Flow**, simples e direto para colaboração em equipe:

1. Crie uma branch a partir da `main`.
2. Faça commits pequenos e objetivos.
3. Abra um Pull Request (PR) para revisão.
4. Aguarde aprovação e faça o merge na `main`.
5. A branch `main` é considerada estável e pode ser implantada em produção.
6. Após o merge, delete a branch para manter o repositório limpo.

---

## Padrões de Arquitetura e Código

- Siga a estrutura de pastas e camadas definida (ex: `api_certify/modules`, `api_certify/repositories`, `api_certify/services`, `api_certify/configs`, etc).
- Mantenha o padrão de injeção de dependência e repository pattern.
- Respeite o princípio da responsabilidade única (cada arquivo deve ter um propósito claro).
- Evite criar novas pastas ou camadas sem discutir antes com o time.
- Nomenclatura consistente: `UserRepository`, `UserService`, `UserController`, etc.
- Sempre implemente testes ou mocks quando adicionar novas regras de negócio.
- Utilize as ferramentas de lint/prettier antes de commitar.

---

## Branches

- Crie uma branch para cada nova feature, fix ou refatoração.
- Nomeie as branches no formato:

  ```
  feat/nome-da-feature
  fix/descricao-do-bug
  chore/ajuste-menor
  refactor/nome-da-refatoracao
  ```

- Sempre crie branches a partir da `main`.
- Após o merge e deploy, delete a branch.

---

## Commits (Semantic Commits)

Siga o padrão de commits semânticos:

```
<tipo>(escopo opcional): descrição curta
```

Tipos comuns:
- `feat:` nova funcionalidade  
- `fix:` correção de bug  
- `docs:` mudança na documentação  
- `style:` formatação, espaçamento, indentação  
- `refactor:` refatoração de código  
- `test:` adição ou ajuste de testes  
- `chore:` tarefas de build, configs, etc  

Exemplos:
```
feat(auth): adiciona login com Google
fix(api): corrige erro de timeout na requisição
docs(readme): atualiza instruções de instalação
```

---

## Pull Requests

- Atualize sua branch com `main` antes de abrir o PR.
- Resolva conflitos localmente antes de enviar.
- Descreva claramente o que foi feito e o motivo.
- PRs pequenos e objetivos são mais fáceis de revisar.
- Solicite revisão de outro desenvolvedor antes do merge.
- Após o merge, delete a branch.

---

## O que evitar

- Commits genéricos como “update” ou “ajustes”.
- Arquivos desnecessários (`node_modules`, `.env`, `dist`, etc) — use `.gitignore`.
- Código sem lint, sem tipagem ou sem testes quando aplicável.
- Alterar padrões estruturais sem alinhamento prévio.

---

## Antes de enviar

- [ ] Rodou os testes e o projeto está funcionando.
- [ ] Passou o lint/prettier.
- [ ] Seguiu os padrões de arquitetura e commit.
- [ ] Branch está atualizada com `main`.
- [ ] PR foi revisado antes do merge.

---

Código limpo, padronizado e bem descrito = projeto escalável e fácil de manter.
