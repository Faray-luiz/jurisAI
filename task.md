# Lista de Tarefas: Redesenho do Chat Livre (Minerva CSRM AI)

- `[x]` 1. Componente de Avatar (OwlAvatar)
  - `[x]` Inserir a função OwlAvatar com SVG vetorial personalizado em page.tsx
- `[x]` 2. Frontend: Estrutura do Chat Livre (page.tsx)
  - `[x]` Isolar a aba de chat livre (`activeTab === "chat"`) da central de missões
  - `[x]` Exibir o cabeçalho de boas-vindas da CSRM AI no topo
  - `[x]` Renderizar o card flutuante de chat com bordas arredondadas e sombra
  - `[x]` Adicionar botão de histórico no topo direito do card
  - `[x]` Implementar mensagem de boas-vindas dinâmica ("Oi [Nome], como posso te ajudar?") com o avatar da Minerva
  - `[x]` Renderizar a lista de diálogos com avatares (Minerva para assistente, iniciais para usuário)
  - `[x]` Inserir disclaimer e input com botão de anexo e botão de envio dourado champagne dentro do card
- `[x]` 3. Frontend: Ajuste de Layout da Central de Missões
  - `[x]` Condicionar a caixa de input global inferior para não aparecer na aba "chat"
- `[x]` 4. Validação & Publicação
  - `[x]` Executar npm run build
  - `[x]` Commitar e push para a branch main
