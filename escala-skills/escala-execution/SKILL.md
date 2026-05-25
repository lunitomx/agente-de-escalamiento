     1|     1|---
     2|     2|description: 'Sub-agente Execution. Guía la decisión de Ejecución: meeting rhythms,
     3|     3|  prioridades, KPIs, Hábitos de Ejecución.'
     4|     4|name: escala-execution
     5|     5|---
     6|     6|
     7|     7|# Escalamiento Execution
     8|     8|
     9|     9|## Purpose
    10|    10|
    11|    11|Entry point del sub-agente de Execution. Evalúa disciplina de ejecución y guía implementación de ritmos y accountability.
    12|    12|
    13|    13|## Context
    14|    14|
    15|    15|**When to use:** Cuando el diagnóstico ruta a Execution, o el usuario quiere mejorar ejecución operativa.
    16|    16|
    17|    17|## Steps
    18|    18|
    19|    19|### Step 1: Load Context
    20|    20|
    21|    21|Leer:
    22|    22|- `.escala/agent/sub-agents/execution.md`
    23|    23|- `.escala/agent/memory/company-profile.yaml`
    24|    24|- `.escala/knowledge/execution/overview.md`
    25|    25|
    26|    26|### Step 2: Check Existing Work
    27|    27|
    28|    28|```bash
    29|    29|ls work/execution/ 2>/dev/null
    30|    30|```
    31|    31|
    32|    32|### Step 3: Recommend Next Tool
    33|    33|
    34|    34|| Estado | Recomendación |
    35|    35||--------|--------------|
    36|    36|| Sin trabajo previo | `/escala-execution-habits` — evaluar 10 hábitos |
    37|    37|| Hábitos de Ejecución hecho | `/escala-execution-rhythms` — diseñar meeting rhythm |
    38|    38|| Rhythms diseñados | `/escala-execution-priorities` — prioridades trimestrales |
    39|    39|| Todo hecho | Re-evaluar Hábitos de Ejecución, medir progreso |
    40|    40|
    41|    41|Los Meeting Rhythms son generalmente el cambio de mayor impacto inmediato.
    42|    42|
    43|    43|### Step 4: Guide
    44|    44|
    45|    45|Enfatizar: "La ejecución perfecta de una estrategia mediocre supera la ejecución mediocre de una estrategia perfecta."
    46|    46|
    47|    47|## Output
    48|    48|
    49|    49|| Item | Destination |
    50|    50||------|-------------|
    51|    51|| Work artifacts | `work/execution/` |
    52|    52|| Next | Skill específico de Execution |
    53|    53|

---
*> Esta herramienta está inspirada en los Hábitos de Ejecución, desarrollados por Verne Harnish como parte de su metodología de escalamiento de negocios. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
