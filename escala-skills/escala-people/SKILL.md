     1|---
     2|description: 'Sub-agente People. Evalúa y guía la decisión de People: personas correctas
     3|  en los asientos correctos, core values, accountability.'
     4|name: escala-people
     5|---
     6|
     7|# Escalamiento People
     8|
     9|## Purpose
    10|
    11|Entry point del sub-agente de People. Evalúa la madurez de People, revisa trabajo existente y guía al siguiente paso concreto.
    12|
    13|## Context
    14|
    15|**When to use:** Cuando el diagnóstico ruta a People, o el usuario pide trabajar en temas de equipo/personas.
    16|
    17|## Steps
    18|
    19|### Step 1: Load Context
    20|
    21|Leer:
    22|- `.escala/agent/sub-agents/people.md` (persona del sub-agente)
    23|- `.escala/agent/memory/company-profile.yaml` (contexto empresa)
    24|- `.escala/knowledge/people/overview.md` (conocimiento del dominio)
    25|
    26|### Step 2: Check Existing Work
    27|
    28|```bash
    29|ls work/people/ 2>/dev/null
    30|```
    31|
    32|Evaluar qué herramientas ya se han completado.
    33|
    34|### Step 3: Recommend Next Tool
    35|
    36|| Estado | Recomendación |
    37||--------|--------------|
    38|| Sin trabajo previo | `/escala-people-fac` — Mapa de Funciones y Responsabilidades |
    39|| FACChart hecho | `/escala-people-values` — Core Values Discovery |
    40|| FACChart + Values | `/escala-people-topgrading` — Proceso de contratación |
    41|| Todo hecho | Revisar gaps, re-evaluar scores |
    42|
    43|### Step 4: Guide
    44|
    45|Adaptar la guía al tamaño y contexto de la empresa. Una startup de 15 personas necesita algo diferente que una empresa de 200.
    46|
    47|Siempre conectar con el "por qué" del libro: sin las personas correctas, la estrategia y ejecución no funcionan.
    48|
    49|## Output
    50|
    51|| Item | Destination |
    52||------|-------------|
    53|| Work artifacts | `work/people/` |
    54|| Next | Skill específico de People |
    55|

---
*Esta herramienta está inspirada en el Mapa de Funciones y Responsabilidades, desarrollado por Verne Harnish. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.*
