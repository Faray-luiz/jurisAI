# Documento de Requisitos do Produto (PRD) — v2.0

## Projeto: JurisAI Gateway – Plataforma Unificada de Inteligência Artificial

**Status:** Revisado (incorpora avaliação arquitetural) **Versão:** 2.0 **Substitui:** PRD v1.0 **Público de aprovação:** Sócios · Compliance · TI · Segurança da Informação

---

### 1\. Visão Geral do Produto

O **JurisAI Gateway** é a plataforma interna centralizada do escritório para interação com Modelos de Linguagem de Grande Porte (LLMs). O sistema unifica o acesso a múltiplos provedores (OpenAI, Anthropic) por trás de uma camada de abstração *model-agnostic*, roteando cada tarefa jurídica para o modelo mais adequado de forma transparente.

A plataforma reduz o risco de erro material por meio de **ancoragem (grounding) determinística** de citações normativas contra fontes autoritativas, assegura o sigilo profissional (LGPD e segredo de justiça) com isolamento por cliente/matéria, e centraliza o controle financeiro, de auditoria e de governança do uso de IA.

**Princípio reitor:** o JurisAI Gateway é uma ferramenta de **apoio** à advocacia, não um substituto do juízo profissional. Nenhum conteúdo gerado é entregue como verdade jurídica sem ancoragem em fonte ou sinalização explícita de "não verificado". A responsabilidade final pela peça é sempre do advogado.

---

### 2\. Objetivos e Critérios de Sucesso (KPIs)

**Nota de revisão:** a meta original de "0% de alucinação" foi removida por ser tecnicamente inatingível (nenhum LLM, mesmo a temperatura 0.0, garante zero citação falsa) e por criar exposição jurídica. Foi substituída por métricas de *verificação* e *controle*, que são mensuráveis e defensáveis.

| KPI | Meta | Como medir |
| :---- | :---- | :---- |
| **Verificação de citações** | ≥ 99% das citações normativas exibidas são ancoradas em fonte autoritativa ou marcadas como "não verificada" | Logs do serviço de grounding |
| **Zero peças externas sem checagem** | 100% das minutas exportadas passam por revisão humana obrigatória antes de uso externo | Trilha de auditoria \+ flag de export |
| **Segurança de dados** | 100% das requisições via APIs corporativas Enterprise (sem uso para treinamento) | Configuração \+ auditoria de chaves |
| **Eficiência de custos** | Redução de ≥ 30% no desperdício de tokens via roteamento \+ cache | Métricas de custo/peça (LangSmith) |
| **Taxa de abstenção saudável** | O sistema deve recusar/abster-se quando não há fonte; meta de abstenção monitorada (não zero) | Logs de grounding |
| **Adoção interna** | Reter ≥ 85% do fluxo diário de análise e escrita após o 1º mês | Analytics de uso |
| **Latência (p95)** | Chat livre ≤ 6s · Peça com grounding ≤ 25s | APM / observabilidade |
| **Disponibilidade** | ≥ 99,5% mensal | Monitoramento de uptime |

---

### 3\. Personas do Usuário

* **Usuário Final (Advogado/Associado):** analisa petições longas, resume linhas do tempo processuais, redige minutas de contestações e contratos. Exige respostas rápidas, precisas, bem formatadas e ancoradas na realidade do processo. **Só enxerga os processos/matérias aos quais tem acesso.**  
* **Administrador (Sócio/Compliance/TI):** monitora custos por advogado/núcleo, audita logs (com PII mascarada), gerencia muralhas éticas entre clientes em conflito, e atualiza as instruções do sistema conforme a jurisprudência muda.  
* **Auditor/Compliance (perfil dedicado):** acesso ao log de auditoria sob controle próprio (segregação de funções — quem usa não é quem audita).

---

### 4\. Requisitos Funcionais

#### 4.1. Interface Unificada de Trabalho (UI/UX)

* **Módulo de Chat Contextual:** interface de chat limpa (estilo Claude/ChatGPT) para interações livres e focadas.  
* **Central de Missões (Templates de Prompt):** botões de tarefas pré-configuradas (ex.: "Análise de Petição Inicial", "Rascunho de Recurso"). O usuário clica, anexa o PDF, e o sistema injeta as instruções de engenharia de prompt. Templates frequentes usam **cache semântico/prompt caching** para reduzir custo.  
* **Seleção Automática de Modelo (Roteador):** o sistema seleciona de forma invisível o modelo ideal por complexidade, custo e latência. O roteador é **model-agnostic**: famílias e versões são configuráveis por *registry*, sem reescrita de código.  
  * **Análise complexa e peças longas:** família Anthropic Claude (topo de linha).  
  * **Tarefas estruturadas, automações e verificação:** família GPT-4o / mini.  
* **Indicador de confiança e fonte:** toda citação normativa exibida mostra se foi **verificada** (com link à fonte) ou **não verificada**. Respostas sem fonte podem ser exibidas como rascunho com aviso visível.

#### 4.2. Governança e Controle Financeiro

* **Autenticação Segura:** login via Microsoft 365 ou Google Workspace com 2FA. **RBAC** com papéis (Advogado, Sócio, Compliance, TI) e **isolamento de acesso por matéria/cliente** (row-level).  
* **Muralha Ética (Ethical Wall):** bloqueio de acesso cruzado entre clientes/processos com conflito de interesse declarado.  
* **Gestão de Cotas de Custo:**  
  * Painel para definir limites orçamentários mensais (USD) por usuário ou núcleo.  
  * **Estimativa de custo pré-voo:** o sistema estima o custo da requisição *antes* de executá-la e verifica a cota, evitando travamento no meio de uma peça.  
  * Alertas em 80% e bloqueio (com grace configurável) em 100%.  
* **Trilha de Auditoria:** registro de todo o histórico (quem enviou, o quê, qual modelo respondeu, custo, e resultado da validação), **com redação/mascaramento de PII** e controle de acesso próprio.

---

### 5\. Requisitos Não-Funcionais e Engenharia de Proteção

#### 5.1. Determinismo e ancoragem

* **Temperatura 0.0** em todos os modelos via API — reduz variância (ressalva: **não** elimina alucinação por si só).  
* **Arquitetura RAG real:** o corpus jurídico curado (legislação \+ jurisprudência) é indexado (embeddings → vector store → reranking). A resposta deve **citar trechos recuperados ou abster-se** ("cite-ou-abstenha"). Instrução de sistema *sozinha* não impede o uso de conhecimento paramétrico — a ancoragem é arquitetural, não textual.

#### 5.2. Camada de Validação Crítica (Guardrails)

1. **Validação de Entrada (prompt):** bloqueia tentativas de fuga de papel (*prompt injection*) no prompt do usuário.  
2. **Sanitização de Documento:** separa **instrução vs. dado** no conteúdo anexado. Petições/PDFs (muitas vezes produzidos pela parte contrária) podem conter instruções injetadas — esta é a maior superfície de ataque e **não** é coberta pela validação do prompt.  
3. **Verificação de Citações (grounding determinístico):** cada citação normativa é checada contra a fonte autoritativa (vector store \+ APIs jurídicas: LexML, DJe, diários oficiais). Se o dispositivo citado não retorna na fonte, a citação é **bloqueada/sinalizada** — não entregue como válida. Um LLM-juiz (ex.: GPT-4o mini) pode complementar, mas **não** é a garantia.  
4. **Validação de Saída:** filtros de não-exposição de PII e dados sensíveis não relacionados.

**Decisão de design (síncrono vs. assíncrono):** a verificação de citações para peças é **síncrona** — a citação só é renderizada após validação. A versão "em segundo plano" do v1 foi descartada porque entregaria conteúdo não verificado à tela antes da checagem, contradizendo o objetivo.

#### 5.3. Resiliência e operação

* **Fallback entre provedores**, retry com backoff exponencial, timeout e circuit breaker.  
* **Versionamento de modelo** via registry \+ harness de avaliação (evals) para trocar versões sem regressão silenciosa.  
* **Orçamento de latência** explícito por tipo de tarefa (ver KPIs).

#### 5.4. Segurança de dados

* **Criptografia em repouso e em trânsito** (TLS). Documentos anexados criptografados.  
* **Residência de dados no Brasil** sempre que aplicável (LGPD).  
* **Política de retenção e exclusão** definida por tipo de dado.  
* **Isolamento por cliente** no storage (sem contaminação cruzada).

---

### 6\. Arquitetura Tecnológica Proposta

* **Frontend:** React.js / Next.js.  
* **Backend:** Python com FastAPI.  
* **Orquestração:** LangChain ou LlamaIndex.  
* **Camada RAG:** embeddings \+ vector store \+ reranker \+ conectores às APIs jurídicas (LexML, DJe, diários).  
* **Identidade:** IdP corporativo (M365 / Google Workspace) com SSO, 2FA e RBAC.  
* **Observabilidade:** LangSmith para auditoria de prompts e custo de tokens, complementado por métricas de negócio (custo/peça, taxa de abstenção, taxa de revisão humana) e alertas.

#### 6.1. Diagrama de Arquitetura (Mermaid)

flowchart TD

    subgraph USR\["Camada de Usuario"\]

        ADV\["Advogado / Associado"\]

        ADM\["Administrador\<br/\>Socio \- Compliance \- TI"\]

    end

    subgraph FE\["Frontend \- Next.js / React"\]

        CHAT\["Modulo de Chat Contextual"\]

        MISSOES\["Central de Missoes\<br/\>Templates de Prompt"\]

        UPLOAD\["Upload de Documentos"\]

        DASH\["Dashboard de Custos e Cotas"\]

    end

    subgraph EDGE\["Borda e Identidade"\]

        WAF\["API Gateway / WAF\<br/\>Rate limit \- TLS"\]

        AUTH\["IdP \- M365 / Google Workspace\<br/\>SSO \+ 2FA \+ RBAC"\]

    end

    subgraph CORE\["Backend de Orquestracao \- FastAPI"\]

        ORCH\["Orquestrador\<br/\>LangChain / LlamaIndex"\]

        GIN\["Guardrail de Entrada\<br/\>Anti Prompt-Injection"\]

        SAN\["Sanitizacao de Documento\<br/\>Separacao Instrucao vs Dado"\]

        COSTPRE\["Estimativa de Custo Pre-voo\<br/\>+ Verificacao de Cota"\]

        ROUTER\["Roteador de Modelos\<br/\>Complexidade \- Custo \- Latencia"\]

        GROUND\["Verificacao de Citacoes\<br/\>Grounding Deterministico"\]

        GOUT\["Guardrail de Saida\<br/\>PII \- Dados Sensiveis"\]

        HITL\["Confianca e Revisao Humana\<br/\>Flag / Abstencao"\]

    end

    subgraph RAG\["Camada RAG \- Fonte Autoritativa"\]

        EMB\["Embeddings"\]

        VDB\[("Vector Store\<br/\>Legislacao \- Jurisprudencia")\]

        RERANK\["Reranker"\]

        LEGALAPI\["APIs Juridicas\<br/\>LexML \- Diarios \- DJe"\]

    end

    subgraph LLM\["Provedores LLM \- APIs Enterprise"\]

        ANTH\["Anthropic\<br/\>Claude familia Opus/Sonnet"\]

        OAI\["OpenAI\<br/\>GPT-4o / mini"\]

    end

    subgraph DATA\["Persistencia e Governanca"\]

        DOCS\[("Storage de Documentos\<br/\>Criptografado \- Isolamento por Cliente")\]

        AUDIT\[("Trilha de Auditoria\<br/\>Logs com Redacao de PII")\]

        QUOTA\[("Servico de Cotas e Billing")\]

        OBS\["Observabilidade\<br/\>LangSmith \- Metricas \- Alertas"\]

    end

    ADV \--\> CHAT

    ADV \--\> MISSOES

    ADV \--\> UPLOAD

    ADM \--\> DASH

    CHAT \--\> WAF

    MISSOES \--\> WAF

    UPLOAD \--\> WAF

    DASH \--\> WAF

    WAF \--\> AUTH

    AUTH \--\> ORCH

    ORCH \--\> GIN

    GIN \--\> SAN

    SAN \--\> COSTPRE

    COSTPRE \--\>|"cota OK"| ROUTER

    COSTPRE \--\>|"cota excedida"| HITL

    ROUTER \--\> EMB

    EMB \--\> VDB

    VDB \--\> RERANK

    RERANK \--\> LEGALAPI

    ROUTER \--\>|"analise complexa"| ANTH

    ROUTER \--\>|"tarefa estruturada / verificacao"| OAI

    ANTH \--\> GROUND

    OAI \--\> GROUND

    RERANK \--\> GROUND

    LEGALAPI \--\> GROUND

    GROUND \--\>|"citacao valida"| GOUT

    GROUND \--\>|"citacao nao encontrada"| HITL

    GOUT \--\> HITL

    HITL \--\> CHAT

    UPLOAD \-.-\> DOCS

    SAN \-.-\> DOCS

    ORCH \-.-\> AUDIT

    GROUND \-.-\> AUDIT

    COSTPRE \-.-\> QUOTA

    QUOTA \-.-\> DASH

    ORCH \-.-\> OBS

    ROUTER \-.-\> OBS

    AUDIT \-.-\> DASH

---

### 7\. Governança e Conformidade

A plataforma adota controles mapeáveis a frameworks reconhecidos de gestão de risco de IA:

* **ISO/IEC 42001 (AI Management System):** ciclo de gestão de risco do modelo, rastreabilidade de decisão e melhoria contínua.  
* **NIST AI RMF:** funções *Govern / Map / Measure / Manage* aplicadas ao roteamento, aos guardrails e ao grounding.  
* **LGPD:** base legal, minimização, residência de dados, retenção/exclusão e direitos do titular.  
* **Ética profissional (OAB):** responsabilidade do advogado sobre a peça final; IA como apoio, com sinalização de conteúdo não verificado.  
* **Suite de avaliação (evals):** *golden datasets* jurídicos para regressão dos guardrails, da qualidade do roteamento e da precisão das citações a cada troca de modelo.

---

### 8\. Plano de Implementação Detalhado

* **Fase 1 — Infraestrutura & Segurança (Semanas 1-2):** ambiente cloud, chaves Enterprise (OpenAI e Anthropic) com termos de não-treinamento ativos, criptografia, residência de dados, IdP \+ RBAC.  
* **Fase 2 — Backend, RAG & Guardrails (Semanas 3-6):** rotas FastAPI, ingestão e indexação do corpus jurídico (RAG), engenharia de prompts, sanitização de documento e **grounding determinístico de citações**.  
* **Fase 3 — Frontend (Semanas 7-8):** telas de chat, upload, indicadores de confiança/fonte e dashboard de custos/cotas.  
* **Fase 4 — Avaliação & Red-Teaming (Semana 9):** testes de prompt injection via documento, isolamento entre clientes, citações falsas e vazamento de PII. Definição dos critérios **go/no-go** com base nessas métricas.  
* **Fase 5 — Monitoramento & Piloto (Semanas 10-11):** integração completa com LangSmith \+ métricas de negócio; piloto com 3 a 5 advogados.  
* **Fase 6 — Homologação & Go-Live (Semana 12):** treinamento, desativação do acesso direto aos portais comerciais nas máquinas do escritório e lançamento oficial.

---

### 9\. Riscos e Mitigações

| Risco | Impacto | Mitigação |
| :---- | :---- | :---- |
| Citação normativa falsa chega ao advogado | Alto (erro material) | Grounding determinístico síncrono \+ revisão humana obrigatória |
| Injeção de instrução via PDF da parte contrária | Alto (manipulação) | Sanitização instrução-vs-dado no conteúdo do documento |
| Vazamento de dados entre clientes | Crítico (sigilo) | Isolamento por matéria \+ muralha ética \+ RBAC |
| Log de auditoria expõe dados privilegiados | Alto (LGPD) | Redação de PII \+ controle de acesso segregado |
| Modelo descontinuado pelo provedor | Médio (operação) | Registry model-agnostic \+ harness de evals \+ fallback |
| Custo descontrolado | Médio (financeiro) | Estimativa pré-voo \+ cache \+ cotas com bloqueio |

---

*Documento de trabalho — sujeito a revisão pelas áreas de Compliance, TI e Segurança da Informação antes da aprovação final.*  
