     1|---
     2|description: 'Sub-agente Strategy. Guía la decisión de Estrategia: core values, BHAG,
     3|  brand promise, Plan Estratégico de Una Página (OPSP), 7 Estratos de Estrategia.'
     4|name: escala-strategy
     5|---
     6|
     7|# Escalamiento Strategy
     8|
     9|## Purpose
    10|
    11|Entry point del sub-agente de Strategy. Evalúa madurez estratégica, verifica prerequisitos y guía hacia la herramienta correcta.
    12|
    13|## Context
    14|
    15|**When to use:** Cuando el diagnóstico ruta a Strategy, o el usuario quiere trabajar en estrategia.
    16|
    17|## Steps
    18|
    19|### Step 1: Load Context
    20|
    21|Leer:
    22|- `.escala/agent/sub-agents/strategy.md`
    23|- `.escala/agent/memory/company-profile.yaml`
    24|- `.escala/knowledge/strategy/overview.md`
    25|
    26|### Step 2: Check Existing Work & Prerequisites
    27|
    28|```bash
    29|ls work/strategy/ 2>/dev/null
    30|ls work/people/ 2>/dev/null
    31|```
    32|
    33|Verificar que People tiene base mínima (score >= 2). Si no, sugerir volver a People primero.
    34|
    35|### Step 3: Recommend Next Tool
    36|
    37|| Estado | Recomendación |
    38||--------|--------------|
    39|| Sin Core Values | `/escala-people-values` primero (prerequisito) |
    40|| Core Values listos, sin Plan Estratégico de Una Página (OPSP) | `/escala-strategy-opsp` — Plan Estratégico de Una Página (Plan Estratégico de Una Página (OPSP)) |
    41|| Plan Estratégico de Una Página (OPSP) básico listo | `/escala-strategy-7strata` — profundizar diferenciación |
    42|| Todo hecho | SWOT/SWT para refinar |
    43|
    44|El Plan Estratégico de Una Página (OPSP) es la pieza central de Strategy. Todo lo demás alimenta al Plan Estratégico de Una Página (OPSP).
    45|
    46|### Step 4: Guide
    47|
    48|Siempre conectar: "La estrategia debe caber en una página. Si no puedes explicarla simple, no está clara."
    49|
    50|## Output
    51|
    52|| Item | Destination |
    53||------|-------------|
    54|| Work artifacts | `work/strategy/` |
    55|| Next | Skill específico de Strategy |
    56|