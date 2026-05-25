     1|---
     2|description: 'Sub-agente Cash. Guía la decisión de Cash: Ciclo de Conversión de Efectivo (CCC), Power
     3|  of One, cash acceleration strategies.'
     4|name: escala-cash
     5|---
     6|
     7|# Escalamiento Cash
     8|
     9|## Purpose
    10|
    11|Entry point del sub-agente de Cash. Evalúa salud financiera operativa y guía optimización del flujo de efectivo.
    12|
    13|## Context
    14|
    15|**When to use:** Cuando el diagnóstico ruta a Cash, o el usuario quiere optimizar flujo de efectivo.
    16|
    17|## Steps
    18|
    19|### Step 1: Load Context
    20|
    21|Leer:
    22|- `.escala/agent/sub-agents/cash.md`
    23|- `.escala/agent/memory/company-profile.yaml`
    24|- `.escala/knowledge/cash/overview.md`
    25|
    26|### Step 2: Check Existing Work
    27|
    28|```bash
    29|ls work/cash/ 2>/dev/null
    30|```
    31|
    32|### Step 3: Recommend Next Tool
    33|
    34|| Estado | Recomendación |
    35||--------|--------------|
    36|| Sin trabajo previo | `/escala-cash-ccc` — mapear Ciclo de Conversión de Efectivo (CCC) |
    37|| CCC mapeado | `/escala-cash-power1` — análisis Análisis Power of One |
    38|| Análisis Power of One hecho | `/escala-cash-acceleration` — estrategias de aceleración |
    39|| Todo hecho | Re-mapear CCC, medir mejoras |
    40|
    41|### Step 4: Guide
    42|
    43|Enfatizar: "El cash es el oxígeno del crecimiento. El crecimiento chupa cash — si no lo gestionas, el éxito mismo puede matarte."
    44|
    45|Nota: Este sub-agente NO da asesoría financiera. Guía el análisis operativo del ciclo de cash usando las herramientas de Escalamiento de Negocios.
    46|
    47|## Output
    48|
    49|| Item | Destination |
    50||------|-------------|
    51|| Work artifacts | `work/cash/` |
    52|| Next | Skill específico de Cash |
    53|

---
*> Esta herramienta está inspirada en el análisis Power of One, desarrollado por Verne Harnish. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.
