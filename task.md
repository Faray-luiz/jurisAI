# Lista de Tarefas: Renomear para CSRM AI e Novo Logotipo

- `[x]` 1. Logotipo & Estilo (globals.css)
  - `[x]` Remover estilo antigo logo-seal e criar nova classe .brand-logo
  - `[x]` Garantir harmonia com o dourado champagne e marrom escuro
- `[x]` 2. Substituição no Frontend (Componentes e Páginas)
  - `[x]` Atualizar Sidebar.tsx (inserir logotipo SVG e texto "CSRM AI")
  - `[x]` Atualizar Topbar.tsx (mudar JurisAI Gateway para CSRM AI)
  - `[x]` Atualizar layout.tsx (mudar metadata title)
  - `[x]` Atualizar page.tsx (mensagens do assistente, cards de bem-vindo, referências do chat livre)
  - `[x]` Atualizar invite/[token]/page.tsx (mudar referências e emoji de balança)
- `[x]` 3. Validação & Deploy
  - `[x]` Rodar npm run build no frontend
  - `[x]` Commitar e push para a branch main
