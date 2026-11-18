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

| ID | Jira | Historia | Depende de |
|----|------|----------|------------|
| S88.1 | ESCALA-120 | Una hoja muestra varios prompts, y el SWT pasa a hoja guiada | — |
| S88.2 | ESCALA-121 | Investigación con fuentes: Vivid Vision, propósito personal y Fanocracy | — |
| S88.3 | ESCALA-122 | Hojas de Propósito de la empresa y Meta grande (BHAG) | S88.1 |
| S88.4 | ESCALA-123 | Hojas de Vivid Vision, Personal Why y Fanocracy | S88.1, S88.2 |
| S88.5 | ESCALA-124 | Prompts 2026: SWT, Actividades, Resumen de visión, Make Change Stick y AI Setup | S88.1 |
| S88.6 | ESCALA-125 | Recorrido del Strategy Day 2026 en orden y mapa de cobertura de las 24 páginas | S88.3, S88.4, S88.5 |

## Decisiones tomadas (Eduardo puede cambiarlas)

- La hoja se llama «Meta grande», no «BHAG» (el Resumen de visión prohíbe la palabra).
- Plazo de la meta grande: 10 a 30 años (workbook 2026).
- Prompt de Fanocracy fiel al workbook (7 de 9 principios); los 9 en la guía.

## Criterios de terminado

- 10 de 10 ejercicios con hoja en español y prompt 2026.
- Prueba de cobertura: 24 de 24 páginas mapeadas.
- Cada hoja nueva: guía con ejemplo real, ≥3 consejos con fuente, vista que se abre sola, guardado md/yaml.
- Gates en verde: pruebas, tipos y lint.
- Listo antes del Strategy Day.
