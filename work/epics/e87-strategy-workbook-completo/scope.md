---
epic_id: E87
title: Strategy workbook completo — todas las herramientas del workbook, con guía, tips y vista visual
status: designed
jira_key: "ESCALA-107"
created: 2026-10-20
designed: 2026-10-20
source: metodologias que debes tener llenadas/EOA Strategy 2025 Participant Workbook (1).pdf
components_touched: conocimiento, coaching/worksheet, coaching/dashboard/boards, escala-skills
change_mode: additive
---

# Scope E87

## Objetivo

Que ESCALA cubra todas las herramientas del workbook de Strategy (38 páginas). Cada herramienta lleva una guía de llenado paso a paso con un ejemplo real, tips profesionales investigados y, al terminar, una vista HTML más su gemelo Markdown. Cierra la brecha que dejó E6 (prometió 34 hojas, cerró con 15).

## Decisiones del dueño y del orquestador (2026-10-20)

- Alcance: solo el workbook de Strategy. People, Execution y Cash quedan fuera.
- El Plan Personal de Una Página y los tableros de visión (p. 30-33) entran.
- Vision Summary: E61 (ESCALA-29) es dueña de la ontología. E87 solo agrega guía de llenado y vista.
- La tarjeta de Caja de arena se corrige según p. 28: DÓNDE, QUÉ, canales y pronóstico a 3-5 años.
- Páginas corregidas: Promesa de marca p. 17-21; preguntas del Cliente central p. 20.
- Fuente canónica del conocimiento: `conocimiento/` (la exportación pública la incluye; excluye `.scaleup/`).
- No se copian imágenes del workbook. El contenido se parafrasea en español y cita página.
- Simple primero: se reutilizan el registro de hojas, el motor `coaching/worksheet/` y el renderizador de E84.

## Criterios de aceptación de cada historia de herramienta (S87.4 a S87.9)

1. Guía de llenado paso a paso, con un ejemplo real (empresa mexicana ficticia pero concreta) en cada paso.
2. Tips profesionales que vienen de S87.3, cada uno con su fuente citada.
3. Al guardar la hoja, se escribe el YAML y se abre una vista HTML autocontenida con su gemelo Markdown.
4. Su prompt de IA del workbook, parafraseado, con número de página.
5. Sus páginas salen de la lista de pendientes de la prueba de cobertura (S87.1).

## Historias

| Historia | Jira | Entrega | Tamaño | Depende de |
|---|---|---|---|---|
| S87.1 | ESCALA-108 | Mapa versionado de las 38 páginas y prueba de cobertura. Lista de pendientes que solo puede encoger. Corrige la tarjeta de Caja de arena (p. 28). Prueba de sincronía `conocimiento/` ↔ `.scaleup/`. Prueba de cero imágenes. | 3 | — |
| S87.2 | ESCALA-109 | Contrato de herramienta: la hoja trae pasos con ejemplo, tips con fuente y prompt. El motor lee el registro instalado. Al guardar escribe YAML + HTML + MD. Se valida con la hoja existente de Cliente central. | 5 | S87.1 |
| S87.3 | ESCALA-110 | `/rai-research` por herramienta (BMC, Strategy Canvas / Océano Azul, Promesa de marca, Cliente central, Actividades diferenciadoras, Vision Summary, Plan Personal). Fuentes trianguladas y citadas. Un archivo de tips por herramienta. | 3 | — (paralela a S87.2) |
| S87.4 | ESCALA-111 | BMC de 9 bloques, puente a Scaling Up (p. 8), lista de verificación (p. 11), prompt (p. 9). | 5 | S87.2, S87.3 |
| S87.5 | ESCALA-112 | Promesa de marca: 1 principal + 2 de apoyo con medida, Count On / Expect / Unique, 3 pruebas, antipromesas y compensaciones, prompt (p. 20). | 3 | S87.2, S87.3 |
| S87.6 | ESCALA-113 | Cliente central: se agregan las 3 preguntas (p. 20) y el prompt (p. 16). Hoja nueva de Actividades diferenciadoras con competidores y 4 ejes (p. 25) y prompt (p. 26). | 5 | S87.2, S87.3 |
| S87.7 | ESCALA-114 | Hoja de Caja de arena con pronóstico a 3-5 años y prompt (p. 28-29). Strategy Canvas de una hoja que junta las 4 piezas ya llenas (p. 7, 12). | 5 | S87.5, S87.6 |
| S87.8 | ESCALA-115 | Hoja de Vision Summary que enlaza `tool.vision-summary` (E61), con guía y vista (p. 35-36). Prompts de cierre de 10 semanas (p. 34). | 2 | S87.7 |
| S87.9 | ESCALA-116 | Plan Personal de Una Página (p. 30-32) y tableros de visión con su prompt (p. 33). | 3 | S87.2, S87.3 |

Total: 9 historias, 34 puntos.

Orden: S87.1 → (S87.2 ∥ S87.3) → S87.4, S87.5, S87.6, S87.9 en cualquier orden → S87.7 → S87.8.

## Criterios de terminado de la épica

- Prueba de cobertura: 38 de 38 páginas mapeadas a un nodo existente o marcadas como no herramienta. La lista de pendientes queda vacía.
- Cada hoja nueva o extendida cumple los 5 criterios de aceptación de arriba, con prueba.
- `conocimiento/registry/worksheets.yaml` lista las hojas nuevas y `total_worksheets` coincide con la lista.
- Ninguna imagen ni PDF del workbook en el repo (prueba).
- `uv run rai gate check --all` pasa.

## Fuera de alcance

- People, Execution y Cash del mismo workbook.
- Nodos nuevos en `ontology/v2/` para Vision Summary (es de E61).
- Reescribir los 5 tableros web de `escala_server/static/dashboards/strategy/`.
- Código que publique un artefacto de Claude. La sesión puede publicar el HTML; el código solo lo escribe en disco.
- Unificar las 18 diferencias previas entre `conocimiento/strategy/` y `.scaleup/knowledge/strategy/`.

### Machine
```yaml
stories:
  - {id: S87.1, jira: ESCALA-108, size: 3, depends_on: []}
  - {id: S87.2, jira: ESCALA-109, size: 5, depends_on: [S87.1]}
  - {id: S87.3, jira: ESCALA-110, size: 3, depends_on: []}
  - {id: S87.4, jira: ESCALA-111, size: 5, depends_on: [S87.2, S87.3]}
  - {id: S87.5, jira: ESCALA-112, size: 3, depends_on: [S87.2, S87.3]}
  - {id: S87.6, jira: ESCALA-113, size: 5, depends_on: [S87.2, S87.3]}
  - {id: S87.7, jira: ESCALA-114, size: 5, depends_on: [S87.5, S87.6]}
  - {id: S87.8, jira: ESCALA-115, size: 2, depends_on: [S87.7]}
  - {id: S87.9, jira: ESCALA-116, size: 3, depends_on: [S87.2, S87.3]}
modules_affected:
  - path: conocimiento/strategy/workbook-coverage.yaml
    change: create
  - path: conocimiento/strategy/worksheets/
    change: modify
  - path: conocimiento/strategy/tools/sandbox.yaml
    change: modify
  - path: conocimiento/registry/worksheets.yaml
    change: modify
  - path: coaching/worksheet/
    change: modify
  - path: coaching/dashboard/boards/render.py
    change: modify
  - path: escala-skills/escala-worksheet/SKILL.md
    change: modify
  - path: tests/test_e87_workbook_coverage.py
    change: create
decisions:
  - id: D1
    choice: "conocimiento/ es la copia canónica; .scaleup/knowledge/strategy/ se sincroniza solo en los archivos que E87 toca"
    rationale: "La exportación pública incluye conocimiento/ y excluye .scaleup/ (tests/test_public_export.py)"
    constraint: "No editar .scaleup/ a mano; copiar desde conocimiento/"
  - id: D2
    choice: "Pendientes de cobertura en lista que solo puede encoger"
    rationale: "S87.1 prueba la brecha sin dejar la suite en rojo; patrón de S86.27"
    constraint: "Ninguna historia agrega páginas a pendientes"
  - id: D3
    choice: "Vision Summary: solo hoja de guía y vista en conocimiento/, enlazada a tool.vision-summary"
    rationale: "E61 (ESCALA-29) es dueña de la ontología"
    constraint: "No tocar ontology/v2/"
constraints:
  - "Cero imágenes o PDF del workbook en el repo"
  - "Todo texto de herramienta en español parafraseado con número de página"
  - "Cada tip cita una fuente de S87.3"
```
