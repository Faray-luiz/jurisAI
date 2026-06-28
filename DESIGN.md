# DESIGN.md - CSRM Advocacia

Constituicao visual do projeto JurisAI remodelada sob o padrao institucional da CSRM Advocacia.

## 1. Identidade e Principios

Conceito: Prestígio e Confiança Corporativa. Reflete o posicionamento multidisciplinar e de alta credibilidade da CSRM Advocacia. O visual é clássico, sóbrio e imponente.

Tom visual: Alabastro limpo + warm charcoal (bronze escuro) + acentos em dourado champagne.

Regras inviolaveis:
- O dourado champagne (#B9A482) é o acento principal e a única cor para CTAs e links ativos.
- O marrom/bronze profundo (#2E251F) é usado para a sidebar (rail) e superfícies escuras.
- O texto principal usa um tom bronze escuro (#332A24).
- Títulos e marcas utilizam a serif clássica Playfair Display.
- A interface, botões e textos de leitura utilizam a geométrica moderna Montserrat.
- Cantos arredondados são refinados e conservadores: 14px em cards/modais, 9px em botões/inputs, 99px em pílulas e badges.

## 2. Paleta de Cores

```css
/* Superficies */
--paper:        #FAF9F6;   /* Alabastro/Off-white quente - fundo da página */
--paper-2:      #F2EFE9;   /* Bege claro - fundo alternativo / hover sutil */
--surface:      #FFFFFF;   /* Branco puro - cards, inputs, áreas de texto */
--line:         #E6DFD5;   /* Bege sutil - divisores, bordas de cards */

/* Tinta */
--ink:          #332A24;   /* Bronze escuro - texto principal */
--ink-soft:     #5C524B;   /* Bronze médio - texto secundário */
--ink-faint:    #8A7E75;   /* Bronze claro - labels, placeholders, metadados */

/* Rail / Sidebar */
--rail:         #2E251F;   /* Bronze profundo - fundo da sidebar */
--rail-2:       #3D332C;   /* Bronze médio-escuro - hover de itens na sidebar */
--rail-line:    #4E423A;   /* Divisores internos da sidebar */
--rail-text:    #C4B9B0;   /* Texto padrão na sidebar */
--rail-bright:  #FAF9F6;   /* Texto ativo na sidebar */

/* Acento primario - Dourado Champagne */
--bordo:        #B9A482;   /* Champagne - CTA principal, destaques, borda ativa */
--bordo-2:      #A08A68;   /* Champagne escuro - hover do dourado */

/* Status: Verificado */
--verde:        #2F6B4F;
--verde-soft:   #E7F0EB;
--verde-line:   #BFD8C9;

/* Status: Nao verificado */
--ambar:        #8C611B;
--ambar-soft:   #F6ECD6;
--ambar-line:   #E2CB97;
```

## 3. Tipografia

- Títulos: Playfair Display
- Interface e Leitura: Montserrat
