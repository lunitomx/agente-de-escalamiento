# E88: Strategy 2026 — scope

jira_key: ESCALA-119

## Objetivo

ESCALA guía los 10 ejercicios del Workbook Strategy 2026 EOA en el orden del Strategy Day, cada uno con su prompt 2026 en español.

## Los 10 ejercicios (orden del taller, agenda p. 2)

1. AI Setup (p. 4)
2. SWT con tendencias 2026/27 (p. 5-6)
3. Actividades diferenciadoras (p. 7-8)
4. Propósito de la empresa (p. 9-11)
5. Meta grande / BHAG (p. 11-14)
6. Vivid Vision (p. 14-16)
7. Fanocracy (p. 17-18)
8. Personal Why (p. 18-19)
9. Resumen de visión (p. 20, 22)
10. Make Change Stick (p. 20)

## Dentro del alcance

- El motor de hojas muestra varios prompts por hoja; la hoja SWT pasa a guiada.
- Hojas nuevas: Propósito, Meta grande, Vivid Vision, Fanocracy, Personal Why (área people).
- Prompts 2026 en SWT, Actividades, Resumen de visión, Make Change Stick y AI Setup.
- Lista de 10 tendencias 2026/2027 (p. 5) en la hoja SWT.
- Investigación con fuentes para Vivid Vision, propósito personal y Fanocracy.
- Recorrido «Strategy Day 2026» en orden y mapa de cobertura de las 24 páginas con prueba.

## Fuera del alcance

- Copiar imágenes o el PDF del workbook al repo.
- Cambiar las hojas del workbook 2025 que no están en el 2026.
- Nodos nuevos en `ontology/v2/`.

## Historias

Diseño: `design.md` (secciones 2–5 y Machine). Tamaños en Fibonacci.

| ID | Jira | Historia | Tamaño | Depende de |
|----|------|----------|--------|------------|
| S88.1 | ESCALA-120 | Una hoja muestra varios prompts, y el SWT pasa a hoja guiada | 5 | — |
| S88.2 | ESCALA-121 | Investigación con fuentes: Vivid Vision, propósito personal y Fanocracy | 3 | — |
| S88.3 | ESCALA-122 | Hojas de Propósito de la empresa y Meta grande (BHAG) | 3 | — |
| S88.4 | ESCALA-123 | Hojas de Vivid Vision, Personal Why y Fanocracy | 5 | S88.1, S88.2, S88.3 (conteos) |
| S88.5 | ESCALA-124 | Prompts 2026: AI Setup, Actividades, Resumen de visión y Make Change Stick | 2 | S88.1 |
| S88.6 | ESCALA-125 | Recorrido del Strategy Day 2026 en orden y mapa de cobertura de las 24 páginas | 5 | S88.3, S88.4, S88.5 |

Orden: S88.1 ∥ S88.2 ∥ S88.3 → S88.5 y S88.4 → S88.6.

### Criterios de aceptación por historia

**S88.1 (ESCALA-120)**
- `ToolGuide` acepta `extra_prompts: [{title, text, at: start|end}]`; `ai_prompt` no cambia.
- Las 21 hojas actuales y las pruebas actuales siguen verdes sin tocarlas.
- `page` se rechaza dentro de cada prompt extra; `title` es obligatorio.
- Prompt `start`: sale bajo el paso 1 y primero en la vista; no en la revisión final.
- Prompt `end`: sale después del principal en la revisión final y en la vista (HTML y MD), con su título.
- `swt.yaml` guiada: pasos `tendencias-2026` (lista de 10 tendencias), `tendencias`, `fortalezas`, `debilidades`, `ideas`; ejemplos «Tortillería El Sol:»; nombre en español con acentos; `summary` en español sin términos vetados.
- `swt.yaml` trae su prompt SWT 2026 como `ai_prompt` y ≥3 tips; el 3.º sale de `work/research/e88-tips/swt.md#fN`.

**S88.2 (ESCALA-121)**
- `work/research/e88-tips/{vivid-vision,life-purpose,fanocracy}.md`.
- Cada archivo: ≥3 hallazgos `### fN`, cada uno con ≥2 fuentes externas citadas.
- Ningún texto copiado del workbook; sin números de página.

**S88.3 (ESCALA-122)**
- `worksheet-core-purpose` y `worksheet-bhag` desde los borradores; nombre visible «Meta grande (BHAG)», plazo 10–30 años.
- Cada hoja pasa `parse_guide`, ≥3 tips con fuente, vista con todos los pasos.
- Registro: 2 entradas, `total_worksheets` 21 → 23. Mapa E6 regenerado; conteos 88/84 → 90/86.

**S88.4 (ESCALA-123)**
- `worksheet-vivid-vision`, `worksheet-fanocracy` (strategy) y `worksheet-life-purpose` (people).
- Vivid Vision: `ai_followups` pasa a `extra_prompts` (3, `at: end`); «Imprímela» va al `how` del último paso; meta a 10–30 años.
- Fanocracy: prompt fiel (7 de 9 principios); los 9 en la guía.
- ≥3 tips por hoja con fuente de S88.2.
- Registro 23 → 26. Mapa E6 regenerado; conteos 90/86 → 93/89.

**S88.5 (ESCALA-124)**
- `swt.yaml`: `extra_prompts` `start` «Arranque con IA» (AI Setup).
- `differentiating-activities.yaml`: prompt 2026.
- `vision-summary.yaml`: `ai_prompt` = Make Change Stick 2026 (con «10 tareas» y «semana»); `extra_prompts` `start` «Tu día en una sola hoja» (Vision Summary); sin BHAG ni «pág».

**S88.6 (ESCALA-125)**
- `next_sheet` en el último paso: swt → differentiating-activities → core-purpose → bhag → vivid-vision → fanocracy → life-purpose → vision-summary.
- `tests/fixtures/workbook-2026-coverage.yaml`: 10 ejercicios en orden y 24 de 24 páginas (hoja o `no_exercise`), `pending: []`.
- `tests/test_e88_workbook_coverage.py` reusa `check_coverage()` de E87 y sigue la cadena.
- `tests/test_e88_strategy_day_path.py`: el dueño llena las 9 hojas en orden; aparecen los 10 prompts y 9 vistas (PAT-227).

## Decisiones tomadas (Eduardo puede cambiarlas)

- Id `worksheet-bhag`; nombre visible «Meta grande (BHAG)». BHAG no está vetada en `governance/public-boundary.yaml`; `opsp.yaml` y `7-strata.yaml` ya la usan. El Resumen de visión sigue sin la palabra.
- Plazo de la meta grande: 10 a 30 años (workbook 2026).
- Prompt de Fanocracy fiel al workbook (7 de 9 principios); los 9 en la guía. Personal Why vive en el área people.
- Páginas solo en el mapa de cobertura (`tests/fixtures/`), nunca en hojas públicas. Sin imágenes ni PDF del workbook.
- Varios prompts: lista `extra_prompts` junto a `ai_prompt` (design.md D1–D3).
- AI Setup y Make Change Stick viven dentro de swt y vision-summary; no tienen hoja propia.

## Criterios de terminado

- 10 de 10 ejercicios con hoja en español y prompt 2026.
- Prueba de cobertura: 24 de 24 páginas mapeadas.
- Prueba de punta a punta del Strategy Day en verde.
- Cada hoja nueva: guía con ejemplo real, ≥3 consejos con fuente, vista que se abre sola, guardado md/yaml.
- Gates en verde: pruebas, tipos y lint.
- Listo el domingo 22-nov-2026 (Strategy Day: lunes 23).

### Machine
```yaml
modules_affected:
  - path: coaching/worksheet/
    change: modify
  - path: conocimiento/strategy/worksheets/
    change: modify
  - path: conocimiento/people/worksheets/life-purpose.yaml
    change: create
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: ontology/v2/e6-migration-map.json
    change: modify
  - path: tests/
    change: modify
  - path: work/research/e88-tips/
    change: create
decisions:
  - id: D1
    choice: "extra_prompts [{title, text, at}] junto a ai_prompt sin cambio"
    rationale: "Compatible: ninguna hoja ni prueba actual cambia"
    constraint: "ai_prompt no se vuelve lista; page rechazado"
  - id: D2
    choice: "Recorrido por next_sheet; orden y 24 páginas en tests/fixtures/workbook-2026-coverage.yaml"
    rationale: "Reusa el motor; páginas fuera de lo público"
    constraint: "Sin yaml de recorrido en conocimiento/; sin páginas en hojas"
  - id: D3
    choice: "worksheet-bhag con nombre «Meta grande (BHAG)», 10–30 años"
    rationale: "BHAG no vetada en public-boundary"
    constraint: "vision-summary.yaml sin BHAG"
constraints:
  - "Cada yaml nuevo en conocimiento/: regenerar e6-migration-map y subir conteos (PAT-222)"
  - "Revisar public-boundary antes de llaves nuevas (PAT-221)"
  - "Prueba de punta a punta del Strategy Day (PAT-227)"
  - "Sin nodos nuevos en ontology/v2/"
  - "Todo implementable al 22-nov-2026"
```
