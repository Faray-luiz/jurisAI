# Lista de Tarefas: Separação de Menu - Chat Livre vs Missões

- `[x]` 1. Sidebar: Atualização de Navegação
  - `[x]` Atualizar interface `SidebarProps` para suportar `activeTab: "chat" | "missoes" | "auditoria"`
  - `[x]` Substituir "Chat & Missões" por dois botões distintos: "Chat Livre" e "Central de Missões"
- `[x]` 2. Frontend: Gestão de Estado e Telas (`page.tsx`)
  - `[x]` Mapear o tipo de `activeTab` para incluir `"missoes"`
  - `[x]` Limpar a missão ativa (`setSelectedMission(null)`) ao clicar em "Chat Livre"
  - `[x]` Ajustar o painel para exibir a galeria de missões estruturadas (sem o card de Chat Livre) na aba de missões
  - `[x]` Ajustar o painel para ir direto ao chat (sem galeria) na aba de "Chat Livre"
- `[x]` 3. Testes & Homologação
  - `[x]` Executar build do frontend
  - `[x]` Realizar commits e push para produção
