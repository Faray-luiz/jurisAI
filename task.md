# Lista de Tarefas: Dashboard de Governança e Observabilidade de IA

- `[x]` 1. Backend: Implementar API de Estatísticas de Governança
  - `[x]` Adicionar rota `/api/v1/admin/governance/stats` em `backend/app/main.py`
  - `[x]` Agregar métricas de custos, volume de chamadas, bloqueios de muralha ética e consumo por processo
- `[x]` 2. Frontend: Sub-aba "governanca"
  - `[x]` Adicionar `"governanca"` em `AdminSubTab` em `Sidebar.tsx` e `page.tsx`
  - `[x]` Incluir o item "Painel Governança" nos itens navegáveis do menu lateral
- `[x]` 3. Frontend: Componente visual do Dashboard de Governança
  - `[x]` Renderizar cards executivos de KPI (Custo, Requisições, Bloqueios)
  - `[x]` Renderizar o gráfico circular SVG de distribuição de uso por provedores (OpenAI, Anthropic, Google)
  - `[x]` Adicionar tabela interativa de "Uso de IA por Processo" mostrando cliente, custo e conformidade
  - `[x]` Adicionar lista de logs e eventos recentes com foco em Muralha Ética
- `[x]` 4. Validação e Push
  - `[x]` Executar `npm run build`
  - `[x]` Compilar e validar a sintaxe do backend Python
