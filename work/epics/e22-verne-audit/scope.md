# Epic Scope: E22 — Verne Buyer Persona Audit

**Status:** Draft
**Dependencies:** E21 (Verne Harnish Board Member)
**Tamaño:** M

## In Scope

Auditoría de usabilidad de Verne Harnish como buyer persona de una PyME
mexicana (Tortillería "El Buen Maíz"). Se usaron todos los skills de Verne
como if fuera la dueña (Doña Lupe) y se detectaron inconsistencias.

## Findings

### Critical (bloquean la experiencia)

| # | Finding | Severity | Component |
|---|---------|:--------:|-----------|
| F1 | **Grafo de conocimiento vacío** — book-knowledge.json nunca ingerido. `entity_count=0` siempre. Verne habla sin contexto del libro. | 🔴 H | `knowledge_ingester` |
| F2 | **"trabajo" en keywords cash causa falsos positivos** — "Mi prima no rinde en el trabajo" clasifica como cash por la palabra "trabajo" (capital de trabajo). | 🔴 H | `verne_handler._CATEGORY_KEYWORDS` |
| F3 | **Misma pregunta = misma respuesta exacta** — sin aleatorización. Preguntar 3 veces seguidas "¿cómo mejoro mi flujo?" da el mismo texto idéntico. | 🔴 H | `verne_handler._VERNE_TEMPLATES` |
| F4 | **"¿Quién eres?" no tiene respuesta** — cae a "general" sin presentación de Verne. | 🟡 M | `verne_handler.ask()` |
| F5 | **board_debate acepta decision vacía** — sin validación de entrada. | 🟡 M | `verne_handler.board_debate()` |

### Medium

| # | Finding | Severity | Component |
|---|---------|:--------:|-----------|
| F6 | **Vocabulario SME/Latam faltante** — "prima", "encargada", "maistro", "local", "tortillería" no están en keywords. Caen a "general". | 🟡 M | `_CATEGORY_KEYWORDS` + `_CATEGORY_KEYWORDS` people |
| F7 | **ROC no está en vocabulario** — "Return on Cash" es término clave de Verne pero no clasifica. | 🟡 M | `_CATEGORY_KEYWORDS` cash |
| F8 | **Sin aleatorización en preguntas** — mismas 4 preguntas, mismo orden, siempre. | 🟢 B | `_VERNE_TEMPLATES` |
| F9 | **CLI help pobre** — solo lista comandos sin descripción contextual. | 🟢 B | `cli.py` |
| F10 | **Sin adaptación PyME** — trata igual a tortillería de 12 personas que a corporación. | 🟢 B | `verne_handler` |
| F11 | **Debate no usa historia previa** — el history se pasa pero no se referencia en la respuesta. | 🟢 B | `board_debate()` |

## Done Criteria

- [ ] F1: book-knowledge.json ingerido en BD (script o endpoint)
- [ ] F2: "trabajo" removido de cash keywords o calificado como "capital de trabajo"
- [ ] F3: aleatorización en selección de preguntas dentro de cada categoría
- [ ] F4: respuesta específica para "quién eres", "quién es Verne"
- [ ] F5: validación de entrada en board_debate (rechazar empty)
- [ ] F6: vocabulario coloquial SME/Latam agregado a keywords
- [ ] F7: ROC/Return on Cash agregado a cash keywords
- [ ] F8-F11: issues menores evaluados y resueltos

## Buyer Persona: Doña Lupe

- Dueña de Tortillería "El Buen Maíz", 5 locales, 12 empleados
- $2M MXN/mes revenue, siempre corta de efectivo
- Contrata por recomendación (prima, hijo, compadre)
- No conoce términos como CCC, BHAG, OPSP
- Habla coloquial: "no rinde", "se descompuso", "no hay maíz"
- Necesita respuestas simples, prácticas, en español de la calle
