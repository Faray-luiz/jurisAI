# DESIGN.md — JurisAI Gateway

Constituição visual do projeto. Consulte este arquivo antes de criar ou editar qualquer componente, tela ou estilo. Nenhuma decisão de cor, tipo ou espaçamento deve ser tomada fora deste documento.

---

## 1\. Identidade & Princípios

**Conceito:** "Cartório moderno" — seriedade jurídica com precisão de produto de tecnologia. Sem gradientes de startup, sem roxo, sem cards flutuantes genéricos.

**Tom visual:** Papel quente \+ ardósia profunda \+ um único acento bordô (lacre/selo). Sobrio durante o dia de trabalho, legível sob qualquer luz de escritório.

**Regras invioláveis:**

- Nunca use mais de uma família de acento (bordô). Sem azuis, laranjas ou verdes como cor primária.  
- O verde e o âmbar existem **somente** para status de citação (verificado / não verificado). Não reutilize-os em outro contexto.  
- Toda superfície de conteúdo usa a fonte de documento (`Newsreader`). UI usa `IBM Plex Sans`. Títulos e marca usam `Fraunces`.  
- Border-radius é conservador: `14px` em cards/modais, `9px` em botões e inputs, `99px` em pills e badges. Nunca `rounded-full` em cards.  
- Sombras são raras e sutis. Apenas elementos elevados (modais, drawers, cards em hover) recebem sombra.

---

## 2\. Paleta de Cores

/\* ── Superfícies ── \*/

\--paper:        \#FAF8F4;   /\* fundo principal — papel quente \*/

\--paper-2:      \#F2EEE6;   /\* fundo alternativo / hover sutil \*/

\--surface:      \#FFFFFF;   /\* cards, inputs, áreas de conteúdo \*/

\--line:         \#E5DDCF;   /\* divisores, bordas de cards \*/

/\* ── Tinta ── \*/

\--ink:          \#1B1E23;   /\* texto principal \*/

\--ink-soft:     \#4A4F57;   /\* texto secundário \*/

\--ink-faint:    \#7C828B;   /\* labels, placeholders, metadados \*/

/\* ── Rail / Sidebar ── \*/

\--rail:         \#14202B;   /\* fundo da sidebar \*/

\--rail-2:       \#1E2E3C;   /\* hover e cards dentro da rail \*/

\--rail-line:    \#2A3B4B;   /\* divisores dentro da rail \*/

\--rail-text:    \#AEB9C4;   /\* texto padrão na rail \*/

\--rail-bright:  \#EEF2F6;   /\* texto em destaque na rail \*/

/\* ── Acento primário — Bordô (lacre) ── \*/

\--bordo:        \#7A2E2E;   /\* CTA principal, destaques, borda ativa \*/

\--bordo-2:      \#974140;   /\* hover do bordô \*/

/\* ── Status: Verificado (somente citações) ── \*/

\--verde:        \#2F6B4F;

\--verde-soft:   \#E7F0EB;

\--verde-line:   \#BFD8C9;

/\* ── Status: Não verificado (somente citações) ── \*/

\--ambar:        \#8C611B;

\--ambar-soft:   \#F6ECD6;

\--ambar-line:   \#E2CB97;

/\* ── Status: Em revisão (somente citações) ── \*/

\--review-bg:    \#EAEFF3;

\--review-text:  \#3E5366;

\--review-line:  \#CBD8E2;

/\* ── Destaque decorativo ── \*/

\--gold:         \#B08D57;   /\* barra de cota, detalhes ornamentais \*/

**Regra de uso:** `--bordo` é a única cor de ação. `--verde`, `--ambar` e `--review-*` são exclusivos do sistema de citações. `--gold` é decorativo — nunca interativo.

---

## 3\. Tipografia

### Famílias

| Papel | Família | Google Fonts |
| :---- | :---- | :---- |
| **Marca / Títulos hero** | Fraunces | `opsz,wght@9..144,400;9..144,500;9..144,600` |
| **Corpo de documento / análise** | Newsreader | `ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400` |
| **UI / Labels / Botões** | IBM Plex Sans | `wght@400;500;600` |

\<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600\&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400\&family=IBM+Plex+Sans:wght@400;500;600\&display=swap" rel="stylesheet"\>

### Escala tipográfica

/\* Títulos — Fraunces \*/

.text-hero    { font-family: 'Fraunces', serif; font-size: clamp(30px, 4.5vw, 44px); font-weight: 400; line-height: 1.08; letter-spacing: \-0.01em; }

.text-title   { font-family: 'Fraunces', serif; font-size: 29px; font-weight: 400; line-height: 1.15; }

.text-section { font-family: 'Fraunces', serif; font-size: 21px; font-weight: 500; line-height: 1.2; }

/\* Documento — Newsreader (corpo das análises) \*/

.text-doc     { font-family: 'Newsreader', serif; font-size: 17px; line-height: 1.62; color: \#26292E; }

.text-lede    { font-family: 'Newsreader', serif; font-size: 18px; line-height: 1.5; color: var(--ink-soft); }

/\* UI — IBM Plex Sans \*/

.text-label   { font-family: 'IBM Plex Sans', sans-serif; font-size: 12px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; }

.text-body    { font-family: 'IBM Plex Sans', sans-serif; font-size: 14px; line-height: 1.5; }

.text-small   { font-family: 'IBM Plex Sans', sans-serif; font-size: 12.5px; color: var(--ink-faint); }

.text-eyebrow { font-family: 'IBM Plex Sans', sans-serif; font-size: 11.5px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--bordo); }

### Regras tipográficas

- Títulos hero em Fraunces weight 400 (não bold). Itálico ocasional em `<em>` para ênfase editorial, na cor `--bordo`.  
- Corpo de análises sempre em Newsreader — faz a peça gerada *parecer um documento*, não uma resposta de chat.  
- Labels de UI, botões e metadados sempre IBM Plex Sans.  
- Nunca misture Fraunces com bold pesado (`600+`) exceto em subtítulos de seção.

---

## 4\. Layout & Grid

### Estrutura principal

┌─────────────────────────────────────────────────────┐

│  Rail (268px fixo)  │  Main (flex: 1\)               │

│                     │  ┌─ Topbar (sticky, 71px) ──┐ │

│  Logo               │  │ Breadcrumb    Actions     │ │

│  Nav                │  └───────────────────────────┘ │

│  Matérias recentes  │  ┌─ Scroll area ─────────────┐ │

│                     │  │                           │ │

│  \[spacer\]           │  │  Wrap (max-w: 860px)      │ │

│                     │  │  padding: 46px 40px       │ │

│  Quota card         │  │                           │ │

│  Me / avatar        │  └───────────────────────────┘ │

└─────────────────────────────────────────────────────┘

.app   { display: grid; grid-template-columns: 268px 1fr; min-height: 100vh; }

.wrap  { max-width: 860px; margin: 0 auto; padding: 46px 40px 120px; }

### Espaçamento (escala 4px)

4px   — gap interno de chips/badges

8px   — gap entre ícone e label

12px  — padding interno de items de nav

14px  — gap entre cards

16px  — padding de cards compactos

20px  — padding padrão de cards

22px  — padding de modais/drawers

40px  — padding lateral do wrap

46px  — padding top do wrap

### Breakpoint mobile

@media (max-width: 900px) {

  .app  { grid-template-columns: 1fr; }

  .rail { position: fixed; left: 0; top: 0; z-index: 70;

          transform: translateX(-100%); transition: transform .3s; width: 268px; }

  .rail.open { transform: none; }

  .wrap { padding: 32px 20px 100px; }

}

---

## 5\. Componentes

### 5.1 Rail / Sidebar

.rail {

  background: var(--rail);

  color: var(--rail-text);

  padding: 22px 16px;

  display: flex; flex-direction: column; gap: 6px;

  position: sticky; top: 0; height: 100vh;

}

- **Logo seal:** `38×38px`, `border-radius: 9px`, `background: linear-gradient(160deg, #7A2E2E, #5e2222)`, sombra interna `rgba(255,255,255,.08)`.  
- **NavItem:** `padding: 9px 10px`, `border-radius: 9px`, hover → `background: var(--rail-2)`.  
- **NavItem ativo:** `background: var(--rail-2)`, cor `var(--rail-bright)`.  
- **Rail label:** `font-size: 10.5px`, `letter-spacing: .13em`, `text-transform: uppercase`, cor `#5E6E7C`.

### 5.2 Topbar

.topbar {

  display: flex; align-items: center; justify-content: space-between;

  padding: 18px 40px;

  border-bottom: 1px solid var(--line);

  background: rgba(250,248,244,.86);

  backdrop-filter: blur(8px);

  position: sticky; top: 0; z-index: 5;

}

### 5.3 Botões

/\* Primário \*/

.btn {

  background: var(--bordo); color: \#fff;

  font-size: 13px; font-weight: 600;

  padding: 11px 18px; border-radius: 9px;

  display: inline-flex; align-items: center; gap: 8px;

  transition: background .15s, transform .1s;

  border: none; cursor: pointer;

}

.btn:hover  { background: var(--bordo-2); }

.btn:active { transform: translateY(1px); }

/\* Secundário / Ghost \*/

.btn.ghost {

  background: var(--surface); color: var(--ink);

  border: 1px solid var(--line);

}

.btn.ghost:hover { background: var(--paper-2); }

Nunca crie variantes com background verde, azul ou amarelo. O único botão primário é bordô.

### 5.4 Cards de missão

.card {

  text-align: left; background: var(--surface);

  border: 1px solid var(--line); border-radius: 14px;

  padding: 20px; position: relative; overflow: hidden;

  transition: transform .18s, box-shadow .18s, border-color .18s;

}

/\* Barra lateral bordô no hover \*/

.card::before {

  content: ""; position: absolute;

  left: 0; top: 0; bottom: 0; width: 3px;

  background: var(--bordo);

  transform: scaleY(0); transform-origin: top;

  transition: transform .2s;

}

.card:hover { transform: translateY(-3px); box-shadow: 0 8px 28px rgba(20,32,43,.08); border-color: \#D8CFBE; }

.card:hover::before { transform: scaleY(1); }

.card .ic {

  width: 34px; height: 34px; border-radius: 9px;

  background: var(--paper-2); color: var(--bordo);

  display: grid; place-items: center; margin-bottom: 14px;

}

.card h3 { font-family: 'Fraunces', serif; font-weight: 500; font-size: 17px; color: var(--ink); margin-bottom: 5px; }

.card p  { font-size: 12.5px; color: var(--ink-faint); line-height: 1.45; }

### 5.5 Chips de citação (elemento-assinatura)

Este é o componente mais importante do sistema. Representa visualmente a verificação de citações que substitui a promessa de "0% de alucinação".

.cite {

  display: inline-flex; align-items: center; gap: 5px;

  font-family: 'IBM Plex Sans', sans-serif;

  font-size: 12.5px; font-weight: 500;

  padding: 1px 8px 1px 7px; border-radius: 7px;

  vertical-align: baseline; white-space: nowrap;

  cursor: pointer; border: 1px solid transparent;

  transition: box-shadow .15s;

}

.cite:hover { box-shadow: 0 2px 8px rgba(20,32,43,.1); }

/\* Verificado — verde \*/

.cite.ok   { background: var(--verde-soft); color: var(--verde); border-color: var(--verde-line); }

/\* Não verificada — âmbar \*/

.cite.warn { background: var(--ambar-soft); color: var(--ambar); border-color: var(--ambar-line); }

/\* Em revisão humana \*/

.cite.review { background: var(--review-bg); color: var(--review-text); border-color: var(--review-line); }

**Estados do chip:** | Estado | Cor | Ícone | Ação ao clicar | |--------|-----|-------|----------------| | `ok` | Verde | ✓ check | Drawer com texto da fonte \+ "Inserir na peça" | | `warn` | Âmbar | ⚠ triangle | Drawer com alerta \+ "Enviar para revisão" | | `review` | Cinza-azulado | ⏱ clock | Drawer com status "aguardando revisão humana" |

### 5.6 Drawer lateral (fonte da citação)

.drawer {

  position: fixed; top: 0; right: 0;

  height: 100vh; width: 430px; max-width: 92vw;

  background: var(--surface);

  box-shadow: 0 24px 60px rgba(20,32,43,.18);

  transform: translateX(102%);

  transition: transform .3s cubic-bezier(.4,0,.1,1);

  z-index: 50;

  display: flex; flex-direction: column;

}

.drawer.open { transform: none; }

/\* Scrim \*/

.scrim {

  position: fixed; inset: 0;

  background: rgba(20,28,37,.42);

  opacity: 0; pointer-events: none;

  transition: opacity .25s; z-index: 40;

}

.scrim.open { opacity: 1; pointer-events: auto; }

- **Cabeçalho:** tag de status (ok/warn) \+ título do dispositivo \+ fonte.  
- **Corpo:** texto recuperado em `blockquote` (Newsreader, borda `3px var(--verde)`) ou caixa de alerta âmbar.  
- **Metadados:** tabela simples — Hierarquia, Vigência, Conferido em, Correspondência.  
- **Rodapé:** botões "Fechar" (ghost) \+ ação primária.

### 5.7 Cards de quota

.quota {

  background: var(--rail-2);

  border: 1px solid var(--rail-line);

  border-radius: 12px; padding: 14px;

}

/\* Barra de progresso \*/

.bar { height: 6px; border-radius: 99px; background: \#0E1922; overflow: hidden; }

.bar \> i { display: block; height: 100%; border-radius: 99px;

           background: linear-gradient(90deg, var(--gold), \#caa978); }

### 5.8 Pills e badges

.pill-router {

  display: flex; align-items: center; gap: 7px;

  font-size: 12px; color: var(--ink-soft);

  background: var(--surface); border: 1px solid var(--line);

  padding: 6px 11px; border-radius: 99px;

}

.pill-router .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--bordo); }

.badge {

  font-size: 11px; font-weight: 600; letter-spacing: .05em;

  text-transform: uppercase; color: var(--bordo);

  background: \#fff; border: 1px solid var(--line);

  padding: 5px 10px; border-radius: 99px;

}

### 5.9 Steps de pipeline

.pstep {

  display: flex; align-items: center; gap: 14px;

  padding: 15px 18px; border: 1px solid var(--line);

  border-radius: 12px; background: var(--surface);

  margin-bottom: 10px; opacity: .45; transition: opacity .3s, border-color .3s;

}

.pstep.active { opacity: 1; border-color: var(--bordo); }

.pstep.done   { opacity: 1; }

.pstep .pic { width: 30px; height: 30px; border-radius: 8px; display: grid; place-items: center; background: var(--paper-2); color: var(--ink-faint); }

.pstep.active .pic { background: var(--bordo); color: \#fff; }

.pstep.done  .pic  { background: var(--verde-soft); color: var(--verde); }

### 5.10 Toast

.toast {

  position: fixed; bottom: 26px; left: 50%;

  transform: translateX(-50%) translateY(20px); opacity: 0;

  background: var(--rail); color: var(--rail-bright);

  font-size: 13px; padding: 13px 20px; border-radius: 11px;

  box-shadow: 0 24px 60px rgba(20,32,43,.18);

  display: flex; align-items: center; gap: 10px;

  transition: .3s; pointer-events: none; z-index: 60;

}

.toast.show { transform: translateX(-50%); opacity: 1; }

---

## 6\. Sombras

\--shadow:    0 1px 2px rgba(20,32,43,.04), 0 8px 28px rgba(20,32,43,.08);   /\* cards em hover \*/

\--shadow-lg: 0 24px 60px rgba(20,32,43,.18);                                 /\* drawer, modal, toast \*/

Nunca use `box-shadow` colorida (ex: `0 4px 12px rgba(122,46,46,.3)`). Sombras são sempre neutras em `rgba(20,32,43,*)`.

---

## 7\. Ícones

Use **somente** ícones de traço (stroke), nunca preenchidos (fill). Estilo: `stroke-width: 1.6` para ícones de interface, `stroke-width: 2` para ícones de status/ação.

Tamanhos padrão:

- `17×17px` — nav rail  
- `16×16px` — dentro de steps e labels  
- `18×18px` — ícones de card  
- `22×22px` — ícones grandes (upload, seal)

Fonte recomendada: Lucide Icons (traço consistente, alinha com o vocabulário visual do sistema).

---

## 8\. Animação

/\* Entrada de views/páginas \*/

@keyframes fade-in {

  from { opacity: 0; transform: translateY(6px); }

  to   { opacity: 1; transform: none; }

}

.view { animation: fade-in .4s ease both; }

/\* Revelar parágrafos do documento \*/

.reveal { opacity: 0; transform: translateY(7px); transition: opacity .5s, transform .5s; }

.reveal.in { opacity: 1; transform: none; }

/\* Spinner de pipeline \*/

@keyframes spin { to { transform: rotate(360deg); } }

.spin { width: 15px; height: 15px; border: 2px solid rgba(122,46,46,.25); border-top-color: var(--bordo); border-radius: 50%; animation: spin .7s linear infinite; }

/\* Regra de redução de movimento — sempre respeitar \*/

@media (prefers-reduced-motion: reduce) {

  \* { animation: none \!important; transition: none \!important; }

  .reveal { opacity: 1; transform: none; }

}

**Princípio:** animação de entrada coesa (um momento orquestrado) \> efeitos espalhados. Hover micro-interactions são bem-vindos; scroll-triggers em elementos de UI são evitados.

---

## 9\. Acessibilidade

- Todo elemento interativo tem `:focus-visible` visível: `outline: 2.5px solid var(--bordo); outline-offset: 2px; border-radius: 4px`.  
- Chips de citação têm `tabindex="0"` e respondem a `Enter`.  
- Drawer tem `role="dialog"` e `aria-label`.  
- Botão de fechar drawer tem `aria-label="Fechar"`.  
- Imagens decorativas têm `aria-hidden="true"`.  
- Contraste mínimo: texto principal (`--ink` sobre `--paper`) passa AA em todos os tamanhos. Texto faint (`--ink-faint`) usado apenas em metadados com `font-size ≥ 12px`.

---

## 10\. O que nunca fazer

| ❌ Proibido | ✅ Alternativa |
| :---- | :---- |
| Gradientes de cor primária em botões | Sólido `--bordo`, hover `--bordo-2` |
| `border-radius` \> 14px em cards | 14px máximo |
| Verde ou âmbar em botões de ação | Apenas bordô como CTA |
| Sombras coloridas | Sombras neutras `rgba(20,32,43,*)` |
| Font-weight 700+ em Fraunces | Máximo 600, preferência 400–500 |
| Texto de documento em IBM Plex Sans | Corpo de análise sempre Newsreader |
| Cards com fundo colorido | Background sempre `--surface` ou `--paper-2` |
| Múltiplos níveis de sombra empilhados | Um nível por elemento elevado |
| Animações em todo scroll | Apenas entrada de view e reveal de parágrafo |
| Ícones preenchidos (fill) | Sempre traço (stroke) |

---

## 11\. Prompt de referência para o LLM (cole no Antigravity)

Use sempre o arquivo `DESIGN.md` como única fonte de verdade para cores, tipografia e componentes. As variáveis CSS em `--` devem ser usadas diretamente; nunca hardcode valores hex diferentes dos definidos neste documento. O único acento interativo é `--bordo` (\#7A2E2E). Verde e âmbar são exclusivos do sistema de chips de citação. A tipografia segue três papéis fixos: Fraunces (marca/títulos), Newsreader (corpo de documento), IBM Plex Sans (UI). Qualquer novo componente deve seguir os padrões de border-radius, sombra e espaçamento da seção 5 antes de ser renderizado.  
