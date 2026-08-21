# Skill Catalog Inventory

Generated from 140 product skills.

## Count by source directory

| Source | Count |
|--------|-------|
| .agents/skills | 39 |
| .claude/skills | 39 |
| escala-skills | 62 |

## Count by decision area

| Area | Count |
|------|-------|
| cash | 15 |
| execution | 18 |
| other | 18 |
| people | 22 |
| session | 54 |
| strategy | 13 |

## Duplicate / near-duplicate groups

Found 39 groups with more than one skill.

### cash

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-cash | escala-skills | cash | 226 | >- |
| scaleup-cash | .agents/skills | cash | 282 | Sub-agente Cash. Guía la decisión de Cash: Cash Conversion Cycle, Power |
| scaleup-cash | .claude/skills | cash | 282 | Sub-agente Cash. Guía la decisión de Cash: Cash Conversion Cycle, Power |

### cash-acceleration

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-cash-acceleration | escala-skills | cash | 178 | Diseña estrategias de aceleración de cash: reducir CCC, mejorar modelo |
| scaleup-cash-acceleration | .agents/skills | cash | 176 | Diseña estrategias de aceleración de cash: reducir CCC, mejorar modelo |
| scaleup-cash-acceleration | .claude/skills | cash | 176 | Diseña estrategias de aceleración de cash: reducir CCC, mejorar modelo |

### cash-ccc

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-cash-ccc | escala-skills | cash | 192 | >- |
| scaleup-cash-ccc | .agents/skills | cash | 154 | Mapea el Cash Conversion Cycle completo: sales cycle, delivery cycle |
| scaleup-cash-ccc | .claude/skills | cash | 154 | Mapea el Cash Conversion Cycle completo: sales cycle, delivery cycle |

### cash-power1

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-cash-power1 | escala-skills | cash | 457 | >- |
| scaleup-cash-power1 | .agents/skills | cash | 155 | Análisis Power of One: impacto de mejorar 1% cada palanca de cash flow. |
| scaleup-cash-power1 | .claude/skills | cash | 155 | Análisis Power of One: impacto de mejorar 1% cada palanca de cash flow. |

### close

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-close | escala-skills | session | 506 | Session close orchestrator. Captures session activity, writes log, validates, an |
| scaleup-close | .agents/skills | session | 512 | Session close orchestrator. Captures session activity, writes log, validates, an |
| scaleup-close | .claude/skills | session | 512 | Session close orchestrator. Captures session activity, writes log, validates, an |

### close-capture

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-close-capture | escala-skills | session | 190 | Collect session activity data from user. Sub-skill of /escala-close. |
| scaleup-close-capture | .agents/skills | session | 183 | Collect session activity data from user. Sub-skill of /scaleup-close. |
| scaleup-close-capture | .claude/skills | session | 183 | Collect session activity data from user. Sub-skill of /scaleup-close. |

### close-log

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-close-log | escala-skills | session | 161 | Write session log file with YAML frontmatter. Sub-skill of /escala-close. |
| scaleup-close-log | .agents/skills | session | 161 | Write session log file with YAML frontmatter. Sub-skill of /scaleup-close. |
| scaleup-close-log | .claude/skills | session | 161 | Write session log file with YAML frontmatter. Sub-skill of /scaleup-close. |

### close-sync

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-close-sync | escala-skills | session | 141 | Sync YAML to markdown views on session close. Sub-skill of /escala-close. |
| scaleup-close-sync | .agents/skills | session | 141 | Sync YAML to markdown views on session close. Sub-skill of /scaleup-close. |
| scaleup-close-sync | .claude/skills | session | 141 | Sync YAML to markdown views on session close. Sub-skill of /scaleup-close. |

### context-add

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-context-add | escala-skills | people | 144 | Add a structured fact to the company knowledge graph. |
| scaleup-context-add | .agents/skills | people | 144 | Add a structured fact to the company knowledge graph. |
| scaleup-context-add | .claude/skills | people | 144 | Add a structured fact to the company knowledge graph. |

### context-query

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-context-query | escala-skills | people | 102 | Query company facts by category from the knowledge graph. |
| scaleup-context-query | .agents/skills | people | 102 | Query company facts by category from the knowledge graph. |
| scaleup-context-query | .claude/skills | people | 102 | Query company facts by category from the knowledge graph. |

### dashboard

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-dashboard | escala-skills | session | 383 | Genera el Progress Dashboard — vista consolidada con scores actuales, historial  |
| scaleup-dashboard | .agents/skills | session | 383 | Genera el Progress Dashboard — vista consolidada con scores actuales, historial  |
| scaleup-dashboard | .claude/skills | session | 383 | Genera el Progress Dashboard — vista consolidada con scores actuales, historial  |

### diagnose

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-diagnose | escala-skills | session | 501 | Diagnóstico completo de la empresa en las 4 decisiones (People, Strategy, Execut |
| scaleup-diagnose | .agents/skills | session | 359 | Diagnóstico completo de la empresa en las 4 decisiones (People, Strategy, Execut |
| scaleup-diagnose | .claude/skills | session | 359 | Diagnóstico completo de la empresa en las 4 decisiones (People, Strategy, Execut |

### execution

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-execution | escala-skills | execution | 193 | Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms, |
| scaleup-execution | .agents/skills | execution | 251 | Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms, |
| scaleup-execution | .claude/skills | execution | 251 | Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms, |

### execution-priorities

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-execution-priorities | escala-skills | execution | 145 | Define prioridades trimestrales, Critical Number y Theme del trimestre. |
| scaleup-execution-priorities | .agents/skills | execution | 145 | Define prioridades trimestrales, Critical Number y Theme del trimestre. |
| scaleup-execution-priorities | .claude/skills | execution | 145 | Define prioridades trimestrales, Critical Number y Theme del trimestre. |

### execution-rhythms

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-execution-rhythms | escala-skills | execution | 145 | Diseña la cadencia de reuniones: daily huddle, weekly, monthly, quarterly |
| scaleup-execution-rhythms | .agents/skills | execution | 144 | Diseña la cadencia de reuniones: daily huddle, weekly, monthly, quarterly |
| scaleup-execution-rhythms | .claude/skills | execution | 144 | Diseña la cadencia de reuniones: daily huddle, weekly, monthly, quarterly |

### execution-rockefeller

**Recommendation:** review manually

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| scaleup-execution-rockefeller | .agents/skills | execution | 145 | Evaluación de los 10 Rockefeller Habits. Diagnóstico de disciplina |
| scaleup-execution-rockefeller | .claude/skills | execution | 145 | Evaluación de los 10 Rockefeller Habits. Diagnóstico de disciplina |

### export

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-export | escala-skills | session | 304 | Genera un Action Plan Export — documento markdown con las 5 secciones clave: dia |
| scaleup-export | .agents/skills | session | 304 | Genera un Action Plan Export — documento markdown con las 5 secciones clave: dia |
| scaleup-export | .claude/skills | session | 304 | Genera un Action Plan Export — documento markdown con las 5 secciones clave: dia |

### goal

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-goal | escala-skills | other | 287 | Set or view the Meta SMART anual. All recommendations filter through this goal. |
| scaleup-goal | .agents/skills | other | 286 | Set or view the SMART annual goal. All recommendations filter through this goal. |
| scaleup-goal | .claude/skills | other | 286 | Set or view the SMART annual goal. All recommendations filter through this goal. |

### level

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-level | escala-skills | other | 197 | Detecta y adapta el nivel de coaching (Shu/Ha/Ri) según scores de diagnóstico. C |
| scaleup-level | .agents/skills | other | 197 | Detecta y adapta el nivel de coaching (Shu/Ha/Ri) según scores de diagnóstico. C |
| scaleup-level | .claude/skills | other | 197 | Detecta y adapta el nivel de coaching (Shu/Ha/Ri) según scores de diagnóstico. C |

### people

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-people | escala-skills | people | 230 | Sub-agente People. Evalúa y guía la decisión de People: personas correctas |
| scaleup-people | .agents/skills | people | 290 | Sub-agente People. Evalúa y guía la decisión de People: personas correctas |
| scaleup-people | .claude/skills | people | 290 | Sub-agente People. Evalúa y guía la decisión de People: personas correctas |

### people-fac

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-people-fac | escala-skills | people | 174 | Guía para crear el Mapa de Funciones y Responsabilidades (FACChart). Clarifica |
| scaleup-people-fac | .agents/skills | people | 169 | Guía para crear el Function Accountability Chart (FACChart). Clarifica |
| scaleup-people-fac | .claude/skills | people | 169 | Guía para crear el Function Accountability Chart (FACChart). Clarifica |

### people-topgrading

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-people-topgrading | escala-skills | people | 155 | Guía el proceso de Topgrading para contratar A-players. Diseña proceso |
| scaleup-people-topgrading | .agents/skills | people | 154 | Guía el proceso de Topgrading para contratar A-players. Diseña proceso |
| scaleup-people-topgrading | .claude/skills | people | 154 | Guía el proceso de Topgrading para contratar A-players. Diseña proceso |

### people-values

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-people-values | escala-skills | people | 211 | Facilita ejercicio de descubrimiento de Core Values. Identifica los |
| scaleup-people-values | .agents/skills | people | 205 | Facilita ejercicio de descubrimiento de Core Values. Identifica los |
| scaleup-people-values | .claude/skills | people | 205 | Facilita ejercicio de descubrimiento de Core Values. Identifica los |

### progress

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-progress | escala-skills | session | 150 | Dashboard de progreso mostrando scores, worksheets completados y próxima acción  |
| scaleup-progress | .agents/skills | session | 150 | Dashboard de progreso mostrando scores, worksheets completados y próxima acción  |
| scaleup-progress | .claude/skills | session | 150 | Dashboard de progreso mostrando scores, worksheets completados y próxima acción  |

### pulse

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-pulse | escala-skills | session | 496 | Realiza el Quarterly Pulse Check — registra el estado de cada decisión (People,  |
| scaleup-pulse | .agents/skills | session | 494 | Realiza el Quarterly Pulse Check — registra el estado de cada decisión (People,  |
| scaleup-pulse | .claude/skills | session | 494 | Realiza el Quarterly Pulse Check — registra el estado de cada decisión (People,  |

### start

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-start | escala-skills | session | 676 | Flujo guiado de inicio a fin: de "hola" a dashboard con recomendación. El agente |
| scaleup-start | .agents/skills | session | 553 | Session start orchestrator. Loads company context, recent sessions, and open tas |
| scaleup-start | .claude/skills | session | 553 | Session start orchestrator. Loads company context, recent sessions, and open tas |

### start-load-profile

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-start-load-profile | escala-skills | session | 154 | Load company profile from YAML. Sub-skill of /escala-start. |
| scaleup-start-load-profile | .agents/skills | session | 154 | Load company profile from YAML. Sub-skill of /scaleup-start. |
| scaleup-start-load-profile | .claude/skills | session | 154 | Load company profile from YAML. Sub-skill of /scaleup-start. |

### start-load-sessions

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-start-load-sessions | escala-skills | session | 154 | Load last 3 session logs. Sub-skill of /escala-start. |
| scaleup-start-load-sessions | .agents/skills | session | 154 | Load last 3 session logs. Sub-skill of /scaleup-start. |
| scaleup-start-load-sessions | .claude/skills | session | 154 | Load last 3 session logs. Sub-skill of /scaleup-start. |

### start-load-tasks

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-start-load-tasks | escala-skills | session | 176 | Load open tasks from task board. Sub-skill of /escala-start. |
| scaleup-start-load-tasks | .agents/skills | session | 176 | Load open tasks from task board. Sub-skill of /scaleup-start. |
| scaleup-start-load-tasks | .claude/skills | session | 176 | Load open tasks from task board. Sub-skill of /scaleup-start. |

### start-present

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-start-present | escala-skills | session | 184 | Present session context summary to user. Sub-skill of /escala-start. |
| scaleup-start-present | .agents/skills | session | 184 | Present session context summary to user. Sub-skill of /scaleup-start. |
| scaleup-start-present | .claude/skills | session | 184 | Present session context summary to user. Sub-skill of /scaleup-start. |

### strategy

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-strategy | escala-skills | strategy | 246 | Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG, |
| scaleup-strategy | .agents/skills | strategy | 359 | Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG, |
| scaleup-strategy | .claude/skills | strategy | 359 | Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG, |

### strategy-7strata

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-strategy-7strata | escala-skills | strategy | 204 | Guía a través de los 7 Estratos de Estrategia para construir diferenciación |
| scaleup-strategy-7strata | .agents/skills | strategy | 275 | Guía a través de los 7 Strata of Strategy para construir diferenciación |
| scaleup-strategy-7strata | .claude/skills | strategy | 275 | Guía a través de los 7 Strata of Strategy para construir diferenciación |

### strategy-opsp

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-strategy-opsp | escala-skills | strategy | 786 | Guía paso a paso para llenar el Plan Estratégico de Una Página (OPSP), la herram |
| scaleup-strategy-opsp | .agents/skills | strategy | 684 | Guía paso a paso para llenar el One-Page Strategic Plan (OPSP), la herramienta |
| scaleup-strategy-opsp | .claude/skills | strategy | 684 | Guía paso a paso para llenar el One-Page Strategic Plan (OPSP), la herramienta |

### strategy-swot

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-strategy-swot | escala-skills | strategy | 169 | Facilita análisis SWOT/SWT para informar la estrategia y el Plan Estratégico de  |
| scaleup-strategy-swot | .agents/skills | strategy | 157 | Facilita análisis SWOT/SWT para informar la estrategia y el OPSP. |
| scaleup-strategy-swot | .claude/skills | strategy | 157 | Facilita análisis SWOT/SWT para informar la estrategia y el OPSP. |

### task-add

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-task-add | escala-skills | session | 151 | Add a task to the Agente de Escalamiento task board with decision and ontology l |
| scaleup-task-add | .agents/skills | session | 148 | Add a task to the ScaleUp task board with decision and ontology links. |
| scaleup-task-add | .claude/skills | session | 148 | Add a task to the ScaleUp task board with decision and ontology links. |

### task-list

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-task-list | escala-skills | session | 123 | Display the current Agente de Escalamiento task board with counts and metadata. |
| scaleup-task-list | .agents/skills | session | 121 | Display the current ScaleUp task board with counts and metadata. |
| scaleup-task-list | .claude/skills | session | 121 | Display the current ScaleUp task board with counts and metadata. |

### task-update

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-task-update | escala-skills | session | 167 | Move a task between states on the Agente de Escalamiento task board. |
| scaleup-task-update | .agents/skills | session | 165 | Move a task between states on the ScaleUp task board. |
| scaleup-task-update | .claude/skills | session | 165 | Move a task between states on the ScaleUp task board. |

### welcome

**Recommendation:** keep-escala | deprecate-scaleup | migrate to core Python when memory is real

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-welcome | escala-skills | session | 828 | Onboarding conversacional sin comandos. "Hola, soy Escala. ¿Qué te preocupa hoy? |
| scaleup-welcome | .agents/skills | session | 261 | Onboarding para ScaleUp Agent AI. Recoge perfil de empresa y prepara contexto pa |
| scaleup-welcome | .claude/skills | session | 261 | Onboarding para ScaleUp Agent AI. Recoge perfil de empresa y prepara contexto pa |

### worksheet

**Recommendation:** merge to escala-* | delete scaleup-* duplicate | port logic to core Python if deterministic

| Skill | Source | Area | Words | Description |
|-------|--------|------|-------|-------------|
| escala-worksheet | escala-skills | other | 267 | Guía paso a paso de worksheets de Escalamiento de Negocios desde la ontología. U |
| scaleup-worksheet | .agents/skills | other | 265 | Guía paso a paso de worksheets de Scaling Up desde la ontología. Usa core Python |
| scaleup-worksheet | .claude/skills | other | 265 | Guía paso a paso de worksheets de Scaling Up desde la ontología. Usa core Python |

## Full catalog

| Skill | Source | Area | Words | Purpose |
|-------|--------|------|-------|---------|
| escala-cash | escala-skills | cash | 226 | Escalamiento Cash |
| escala-cash-acceleration | escala-skills | cash | 178 | Escalamiento Cash — Cash Acceleration Strategies |
| escala-cash-ccc | escala-skills | cash | 192 | Escalamiento Cash — CCC (Ciclo de Efectivo) |
| escala-cash-finanzas | escala-skills | cash | 584 | Escalamiento Cash — De tus Estados Financieros al Power of One |
| escala-cash-power1 | escala-skills | cash | 457 | Escalamiento Cash — Power of One (7 Palancas) |
| escala-memory | escala-skills | cash | 568 | Escalamiento — Memoria Longitudinal |
| escala-memory-alerts | escala-skills | cash | 710 | Escalamiento — Detección de Patrones y Alertas |
| scaleup-cash | .agents/skills | cash | 282 | ScaleUp Cash |
| scaleup-cash | .claude/skills | cash | 282 | ScaleUp Cash |
| scaleup-cash-acceleration | .agents/skills | cash | 176 | ScaleUp Cash — Cash Acceleration Strategies |
| scaleup-cash-acceleration | .claude/skills | cash | 176 | ScaleUp Cash — Cash Acceleration Strategies |
| scaleup-cash-ccc | .agents/skills | cash | 154 | ScaleUp Cash — Cash Conversion Cycle |
| scaleup-cash-ccc | .claude/skills | cash | 154 | ScaleUp Cash — Cash Conversion Cycle |
| scaleup-cash-power1 | .agents/skills | cash | 155 | ScaleUp Cash — Power of One |
| scaleup-cash-power1 | .claude/skills | cash | 155 | ScaleUp Cash — Power of One |
| escala-execution | escala-skills | execution | 193 | Escalamiento Execution |
| escala-execution-habits | escala-skills | execution | 150 | Escalamiento Execution — Hábitos de Ejecución Checklist |
| escala-execution-pipeline | escala-skills | execution | 502 | Escalamiento Execution — De tu Pipeline al Scorecard de Ventas |
| escala-execution-pizarron | escala-skills | execution | 425 | Escalamiento Execution — De la Foto del Pizarrón a tus Métricas |
| escala-execution-prioridad | escala-skills | execution | 435 | Escalamiento Execution — Prioridad #1 y Tema del Trimestre |
| escala-execution-priorities | escala-skills | execution | 145 | Escalamiento Execution — Quarterly Priorities |
| escala-execution-rhythms | escala-skills | execution | 145 | Escalamiento Execution — Meeting Rhythms |
| escala-rhythm-quarterly | escala-skills | execution | 566 | Escalamiento Execution — Quarterly Off-site Automation |
| escala-rhythm-setup | escala-skills | execution | 508 | Escalamiento Execution — Setup de Ritmos |
| escala-rhythm-weekly | escala-skills | execution | 524 | Escalamiento Execution — Weekly Meeting Prep |
| scaleup-execution | .agents/skills | execution | 251 | ScaleUp Execution |
| scaleup-execution | .claude/skills | execution | 251 | ScaleUp Execution |
| scaleup-execution-priorities | .agents/skills | execution | 145 | ScaleUp Execution — Quarterly Priorities |
| scaleup-execution-priorities | .claude/skills | execution | 145 | ScaleUp Execution — Quarterly Priorities |
| scaleup-execution-rhythms | .agents/skills | execution | 144 | ScaleUp Execution — Meeting Rhythms |
| scaleup-execution-rhythms | .claude/skills | execution | 144 | ScaleUp Execution — Meeting Rhythms |
| scaleup-execution-rockefeller | .agents/skills | execution | 145 | ScaleUp Execution — Rockefeller Habits Checklist |
| scaleup-execution-rockefeller | .claude/skills | execution | 145 | ScaleUp Execution — Rockefeller Habits Checklist |
| escala-board | escala-skills | other | 504 | Escalamiento — Board Proactivo Trimestral |
| escala-bugreport | escala-skills | other | 703 | Reporte anónimo de bug o mejora |
| escala-discover | escala-skills | other | 548 | Escalamiento — Discovery de Fuentes de Datos |
| escala-evidence | escala-skills | other | 410 | ESCALA — Armar el paquete de evidencia |
| escala-goal | escala-skills | other | 287 | Escalamiento Goal — SMART Annual Goal |
| escala-health | escala-skills | other | 286 | escala-health |
| escala-level | escala-skills | other | 197 | Escalamiento Level |
| escala-responder | escala-skills | other | 261 | ESCALA — Entregar la respuesta ejecutiva |
| escala-reviewer | escala-skills | other | 455 | ESCALA — Revisar antes de responder |
| escala-selector | escala-skills | other | 586 | ESCALA — Elegir la herramienta adecuada |
| escala-update | escala-skills | other | 419 | escala-update |
| escala-worksheet | escala-skills | other | 267 | Escalamiento Worksheet |
| scaleup-goal | .agents/skills | other | 286 | ScaleUp Goal — SMART Annual Goal |
| scaleup-goal | .claude/skills | other | 286 | ScaleUp Goal — SMART Annual Goal |
| scaleup-level | .agents/skills | other | 197 | ScaleUp Level |
| scaleup-level | .claude/skills | other | 197 | ScaleUp Level |
| scaleup-worksheet | .agents/skills | other | 265 | ScaleUp Worksheet |
| scaleup-worksheet | .claude/skills | other | 265 | ScaleUp Worksheet |
| escala-board-acta | escala-skills | people | 446 | Escalamiento — Acta de Board + Carta al CEO |
| escala-context-add | escala-skills | people | 144 | Add Company Context |
| escala-context-query | escala-skills | people | 102 | Query Company Context |
| escala-decision | escala-skills | people | 459 | ESCALA — Aclarar la decisión |
| escala-people | escala-skills | people | 230 | Escalamiento People |
| escala-people-fac | escala-skills | people | 174 | Escalamiento People — Mapa de Funciones y Responsabilidades |
| escala-people-organigrama | escala-skills | people | 492 | Escalamiento People — De tu Organigrama al FACe |
| escala-people-topgrading | escala-skills | people | 155 | Escalamiento People — Topgrading |
| escala-people-values | escala-skills | people | 211 | Escalamiento People — Core Values Discovery |
| escala-qualifier | escala-skills | people | 172 | ESCALA — Calificar las cuatro decisiones |
| scaleup-context-add | .agents/skills | people | 144 | Add Company Context |
| scaleup-context-add | .claude/skills | people | 144 | Add Company Context |
| scaleup-context-query | .agents/skills | people | 102 | Query Company Context |
| scaleup-context-query | .claude/skills | people | 102 | Query Company Context |
| scaleup-people | .agents/skills | people | 290 | ScaleUp People |
| scaleup-people | .claude/skills | people | 290 | ScaleUp People |
| scaleup-people-fac | .agents/skills | people | 169 | ScaleUp People — Function Accountability Chart |
| scaleup-people-fac | .claude/skills | people | 169 | ScaleUp People — Function Accountability Chart |
| scaleup-people-topgrading | .agents/skills | people | 154 | ScaleUp People — Topgrading |
| scaleup-people-topgrading | .claude/skills | people | 154 | ScaleUp People — Topgrading |
| scaleup-people-values | .agents/skills | people | 205 | ScaleUp People — Core Values Discovery |
| scaleup-people-values | .claude/skills | people | 205 | ScaleUp People — Core Values Discovery |
| escala-close | escala-skills | session | 506 | Escalamiento Close — Session Orchestrator |
| escala-close-capture | escala-skills | session | 190 | Capture Session Activity |
| escala-close-log | escala-skills | session | 161 | Write Session Log |
| escala-close-sync | escala-skills | session | 141 | Sync State to Markdown Views |
| escala-dashboard | escala-skills | session | 383 | Escalamiento Dashboard |
| escala-diagnose | escala-skills | session | 501 | Escalamiento Diagnose |
| escala-export | escala-skills | session | 304 | Escalamiento Export |
| escala-progress | escala-skills | session | 150 | Escalamiento Progress |
| escala-pulse | escala-skills | session | 496 | Escalamiento Pulse |
| escala-start | escala-skills | session | 676 | Escalamiento — Primer Diagnóstico en 10 Minutos |
| escala-start-load-profile | escala-skills | session | 154 | Load Company Profile |
| escala-start-load-sessions | escala-skills | session | 154 | Load Recent Sessions |
| escala-start-load-tasks | escala-skills | session | 176 | Load Open Tasks |
| escala-start-present | escala-skills | session | 184 | Present Session Context |
| escala-task-add | escala-skills | session | 151 | Add Task |
| escala-task-list | escala-skills | session | 123 | List Tasks |
| escala-task-update | escala-skills | session | 167 | Update Task |
| escala-welcome | escala-skills | session | 828 | Escalamiento — Bienvenida Conversacional |
| scaleup-close | .agents/skills | session | 512 | ScaleUp Close — Session Orchestrator |
| scaleup-close | .claude/skills | session | 512 | ScaleUp Close — Session Orchestrator |
| scaleup-close-capture | .agents/skills | session | 183 | Capture Session Activity |
| scaleup-close-capture | .claude/skills | session | 183 | Capture Session Activity |
| scaleup-close-log | .agents/skills | session | 161 | Write Session Log |
| scaleup-close-log | .claude/skills | session | 161 | Write Session Log |
| scaleup-close-sync | .agents/skills | session | 141 | Sync State to Markdown Views |
| scaleup-close-sync | .claude/skills | session | 141 | Sync State to Markdown Views |
| scaleup-dashboard | .agents/skills | session | 383 | ScaleUp Dashboard |
| scaleup-dashboard | .claude/skills | session | 383 | ScaleUp Dashboard |
| scaleup-diagnose | .agents/skills | session | 359 | ScaleUp Diagnose |
| scaleup-diagnose | .claude/skills | session | 359 | ScaleUp Diagnose |
| scaleup-export | .agents/skills | session | 304 | ScaleUp Export |
| scaleup-export | .claude/skills | session | 304 | ScaleUp Export |
| scaleup-progress | .agents/skills | session | 150 | ScaleUp Progress |
| scaleup-progress | .claude/skills | session | 150 | ScaleUp Progress |
| scaleup-pulse | .agents/skills | session | 494 | ScaleUp Pulse |
| scaleup-pulse | .claude/skills | session | 494 | ScaleUp Pulse |
| scaleup-start | .agents/skills | session | 553 | ScaleUp Start — Session Orchestrator |
| scaleup-start | .claude/skills | session | 553 | ScaleUp Start — Session Orchestrator |
| scaleup-start-load-profile | .agents/skills | session | 154 | Load Company Profile |
| scaleup-start-load-profile | .claude/skills | session | 154 | Load Company Profile |
| scaleup-start-load-sessions | .agents/skills | session | 154 | Load Recent Sessions |
| scaleup-start-load-sessions | .claude/skills | session | 154 | Load Recent Sessions |
| scaleup-start-load-tasks | .agents/skills | session | 176 | Load Open Tasks |
| scaleup-start-load-tasks | .claude/skills | session | 176 | Load Open Tasks |
| scaleup-start-present | .agents/skills | session | 184 | Present Session Context |
| scaleup-start-present | .claude/skills | session | 184 | Present Session Context |
| scaleup-task-add | .agents/skills | session | 148 | Add Task |
| scaleup-task-add | .claude/skills | session | 148 | Add Task |
| scaleup-task-list | .agents/skills | session | 121 | List Tasks |
| scaleup-task-list | .claude/skills | session | 121 | List Tasks |
| scaleup-task-update | .agents/skills | session | 165 | Update Task |
| scaleup-task-update | .claude/skills | session | 165 | Update Task |
| scaleup-welcome | .agents/skills | session | 261 | ScaleUp Welcome |
| scaleup-welcome | .claude/skills | session | 261 | ScaleUp Welcome |
| escala-strategy | escala-skills | strategy | 246 | Escalamiento Strategy |
| escala-strategy-7strata | escala-skills | strategy | 204 | Escalamiento Strategy — 7 Estratos de Estrategia |
| escala-strategy-opsp | escala-skills | strategy | 786 | Escalamiento Strategy — Plan Estratégico de Una Página (OPSP) |
| escala-strategy-swot | escala-skills | strategy | 169 | Escalamiento Strategy — SWOT Analysis |
| escala-strategy-swt | escala-skills | strategy | 371 | Escalamiento Strategy — SWT Automático |
| scaleup-strategy | .agents/skills | strategy | 359 | ScaleUp Strategy |
| scaleup-strategy | .claude/skills | strategy | 359 | ScaleUp Strategy |
| scaleup-strategy-7strata | .agents/skills | strategy | 275 | ScaleUp Strategy — 7 Strata of Strategy |
| scaleup-strategy-7strata | .claude/skills | strategy | 275 | ScaleUp Strategy — 7 Strata of Strategy |
| scaleup-strategy-opsp | .agents/skills | strategy | 684 | ScaleUp Strategy — OPSP |
| scaleup-strategy-opsp | .claude/skills | strategy | 684 | ScaleUp Strategy — OPSP |
| scaleup-strategy-swot | .agents/skills | strategy | 157 | ScaleUp Strategy — SWOT Analysis |
| scaleup-strategy-swot | .claude/skills | strategy | 157 | ScaleUp Strategy — SWOT Analysis |