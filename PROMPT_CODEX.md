# Codex — kickoff prompt (copy text below)

Você vai atuar como engenheiro de software sênior responsável por implementar a **Fase 1 (MVP)** do projeto ForgeBoard neste repositório.

ANTES DE CODAR:
1. Inspecione os arquivos existentes e leia `AGENTS.md`, `backend/AGENTS.md`, `frontend/AGENTS.md`, `infra/AGENTS.md`, `docs/PROJECT_SPEC.md` e `docs/ROADMAP.md`.
2. Resuma em poucas linhas o escopo, a arquitetura e os principais riscos técnicos, e defina um plano de execução por pequenos marcos verificáveis.
3. Se o repositório contiver apenas os arquivos de instruções, faça o scaffold necessário. Se já houver código, preserve o que funciona e adapte o plano.

OBJETIVO DESTA EXECUÇÃO:
Entregar uma aplicação local utilizável, com cadastro/login/logout, projetos e issues por usuário, filtros de issues, dashboard e isolamento entre contas, implementada com FastAPI + PostgreSQL + SQLAlchemy/Alembic e React + TypeScript + Vite. Deve subir localmente com Docker Compose, conter testes e documentação. Os detalhes e os critérios de aceite estão em `docs/PROJECT_SPEC.md`.

REGRAS DE EXECUÇÃO:
- Implemente de verdade; não encerre apenas com uma proposta de arquitetura, pseudocódigo ou TODOs.
- Trabalhe em incrementos end-to-end: base do projeto e banco; autenticação; projetos/issues; frontend; testes e documentação.
- Segurança desde o início: senha com Argon2id, sessão opaca em cookie HttpOnly, CSRF para operações autenticadas que alteram estado, autorização no backend e nenhum segredo no repositório.
- Preserve escopo enxuto. Não implemente as fases 2–5 agora: sem cloud paga, Terraform apply, Kubernetes, integração GitHub Actions, Grafana ou scans externos nesta execução.
- Não introduza bibliotecas desnecessárias. Priorize nomes claros, manutenibilidade e commits/alterações pequenas e verificáveis.
- Se uma decisão estiver aberta na spec, escolha a opção mais simples e segura, registre a escolha em `docs/ARCHITECTURE.md` e siga em frente.
- Mantenha README atualizado com instruções reais para instalar, rodar, migrar, testar e encerrar o ambiente.

VALIDAÇÃO OBRIGATÓRIA:
1. Configure o ambiente de desenvolvimento local e tente subir a stack com `docker compose up --build` quando Docker estiver disponível.
2. Execute migrações e os testes reais; corrija falhas causadas pelas suas alterações.
3. Execute linters e verificações de tipo disponíveis no projeto.
4. Demonstre, com testes e/ou passos reproduzíveis, que um usuário A não consegue ler ou alterar projetos/issues do usuário B.
5. Se alguma ferramenta (Docker, rede, dependência) estiver indisponível, não invente sucesso: descreva exatamente o que ficou sem validação.

CRITÉRIO DE CONCLUSÃO:
- Estrutura completa e consistente no repositório, com código executável, testes e README.
- Interface pronta para demonstrar: cadastro -> login -> criar projeto -> criar issue -> filtrar/alterar status -> dashboard -> logout.
- Nenhuma alteração destrutiva externa nem custo em cloud.

No final, informe os arquivos principais criados, a arquitetura, as decisões de segurança, os comandos exatos para reproduzir, os testes executados e resultados, quaisquer limitações e o que ficou para a fase 2. Comece agora pela inspeção dos arquivos e prossiga com a implementação.
