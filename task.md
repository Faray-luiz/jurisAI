# Lista de Tarefas: Eliminação de Ícones e Diálogos Limpos (Minerva CSRM AI)

- `[/]` 1. Backend: Atualizar System Prompt no DB
  - `[ ]` Atualizar o script de seed para o novo prompt de chat_livre sem emojis
  - `[ ]` Atualizar a linha correspondente no banco de dados SQLite de produção
- `[ ]` 2. Backend: Higienização Dinâmica de Texto (Remover Emojis)
  - `[ ]` Criar função no backend para filtrar e remover símbolos unicode/emojis das respostas do LLM
- `[ ]` 3. Frontend: Limpeza da UI (page.tsx)
  - `[ ]` Remover ícone Sparkles do cabeçalho superior do Chat Livre
  - `[ ]` Ocultar metadados técnicos (ícone de CPU, nome de modelo e custo) abaixo dos balões da Minerva
- `[ ]` 4. Validação & Publicação
  - `[ ]` Executar npm run build
  - `[ ]` Commitar e push para a branch main
