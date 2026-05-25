     1|---
     2|description: 'Guía para crear el Mapa de Funciones y Responsabilidades (FACChart). Clarifica
     3|  estructura organizacional, roles y accountability.'
     4|name: escala-people-fac
     5|---
     6|
     7|# Escalamiento People — Mapa de Funciones y Responsabilidades
     8|
     9|## Purpose
    10|
    11|Guiar al usuario para crear su FACChart: identificar todas las funciones del negocio, asignar UN accountable por función, y definir KPIs.
    12|
    13|## Steps
    14|
    15|### Step 1: Load Context
    16|
    17|Leer `.escala/agent/memory/company-profile.yaml` y `.escala/knowledge/people/tools/function-accountability-chart.md`.
    18|Cargar template `templates/function-accountability-chart.md`.
    19|
    20|### Step 2: Identify Functions
    21|
    22|Preguntar: "¿Cuáles son las funciones principales de tu empresa?" Guiar con las funciones estándar como base y adaptar a su industria.
    23|
    24|### Step 3: Assign Accountability
    25|
    26|Para cada función, preguntar quién es accountable. Reglas:
    27|- Exactamente 1 persona por función
    28|- Máximo 2-3 funciones por persona
    29|- El CEO no puede ser accountable de todo
    30|
    31|### Step 4: Define KPIs
    32|
    33|Para cada función, definir 1-2 KPIs medibles semanalmente.
    34|
    35|### Step 5: Validate & Save
    36|
    37|Correr checklist de validación. Guardar en `work/people/fac-chart.md`.
    38|
    39|## Output
    40|
    41|| Item | Destination |
    42||------|-------------|
    43|| FACChart | `work/people/fac-chart.md` |
    44|| Next | `/escala-people-values` o `/escala-people` |
    45|

---
*Esta herramienta está inspirada en el Mapa de Funciones y Responsabilidades, desarrollado por Verne Harnish. Ver [ATTRIBUTIONS.md](../ATTRIBUTIONS.md) para la referencia completa.*
