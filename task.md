# Lista de Tarefas: Eliminação de Ícones e Diálogos Limpos (Minerva CSRM AI)

- `[x]` 1. Backend: Atualizar System Prompt no DB
  - `[x]` Atualizar o script de seed para o novo prompt de chat_livre sem emojis
  - `[x]` Atualizar a linha correspondente no banco de dados SQLite de produção
- `[x]` 2. Backend: Higienização Dinâmica de Texto (Remover Emojis)
  - `[x]` Criar função no backend para filtrar e remover símbolos unicode/emojis das respostas do LLM
- `[x]` 3. Frontend: Limpeza da UI (page.tsx)
  - `[x]` Remover ícone Sparkles do cabeçalho superior do Chat Livre
  - `[x]` Ocultar metadados técnicos (ícone de CPU, nome de modelo e custo) abaixo dos balões da Minerva
- `[x]` 4. Admin e Alinhamento de Prompts (Fonte da Verdade)
  - `[x]` Ocultar o agente de fallback 'default' e renomear 'chat_livre' para 'Chat Global (Minerva)' no painel de administração para eliminar duplicidade de opções.
  - `[x]` Implementar gerador dinâmico de respostas simuladas (`get_mock_response` em `router.py`) que usa o System Prompt cadastrado na plataforma como fonte de verdade para a Minerva em modo simulação.
- `[x]` 5. Validação & Publicação
  - `[x]` Executar npm run build
  - `[x]` Commitar e push para a branch main
