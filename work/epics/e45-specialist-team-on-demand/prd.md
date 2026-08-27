---
epic_id: "E45"
title: "PRD — Especialistas internos bajo demanda"
status: "in_progress"
depends_on: ["E44", "E49"]
---

# PRD E45 — Especialistas internos bajo demanda

## Problema

Un solo análisis es suficiente para una pregunta simple, pero puede perder una
restricción cuando caja, operación, personas y estrategia se afectan entre sí.
Exponer cuatro asistentes al empresario resuelve mal el problema: multiplica
la conversación, duplica contexto y deja al dueño arbitrando opiniones.

## Resultado para el empresario

El empresario habla únicamente con **Escala**. Ante un caso complejo recibe una
sola recomendación ejecutiva que separa hechos, supuestos, desacuerdos, riesgos
y la siguiente acción. Nunca debe escoger un “bot de Cash” ni leer un debate
interno.

## Contrato de experiencia

1. Un router conserva las preguntas simples con un solo coach.
2. Sólo activa los especialistas que aportan a la decisión: Cash, Execution,
   People y/o Strategy.
3. Cada rol recibe una ficha mínima: pregunta, decisión, evidencia pertinente,
   frescura, huecos y límites; no todo el historial de la empresa.
4. Un crítico se activa cuando exista supuesto material o recomendación
   riesgosa; un verificador cuando haya cifra, periodo, fuente o cálculo que
   pueda invalidar la síntesis.
5. La síntesis muestra lo acordado, lo disputado y la pregunta que resolvería
   el desacuerdo. No decide por el dueño.
6. La colaboración es secuencial por defecto; paralelismo sólo se adopta si la
   calificación demuestra menor latencia sin perder trazabilidad.

## Contrato de salida por caso

```yaml
recommendation:
  status: ready | needs_evidence | blocked
  primary_constraint: string | null
  alternatives: []
  evidence_ids: []
  assumptions: []
  disagreements: []
  risks: []
  owner_suggestion: string | null
  next_action: string
  review_cadence: string | null
```

`ready` no autoriza ejecución autónoma. `needs_evidence` y `blocked` deben
formular una pregunta concreta, no rellenar huecos con inferencias.

## Criterios de activación

El equipo se justifica si hay dos o más decisiones relevantes, contradicción de
fuentes, riesgo material, bloqueo del análisis base o solicitud explícita de
revisión transversal. Una métrica, archivo o tarea aislada no lo justifica.

## No objetivos

- Cuatro chats permanentes o avatares con personalidad propia.
- Un servicio central, memoria compartida implícita o agentes en segundo plano.
- Votación por mayoría, decisiones laborales/financieras autónomas o evidencia
  inventada.
- Research como quinto agente público; research es una capacidad invocable por
  el especialista pertinente y conserva fuentes/fecha.

## Medición y aceptación

- Caso simple: no hay coste ni demora de equipo innecesario.
- Caso Cash + Execution: se detecta al menos un riesgo que el análisis simple
  no explicitó, o se demuestra honestamente que no agrega valor.
- Caso Strategy + Cash: un conflicto de precio/margen queda visible y bloquea
  una recomendación falsa.
- Caso People: el rol no infiere rasgos ni toma decisiones de empleo.
- Cada salida conserva evidencia, supuestos y la pregunta pendiente.
- Prueba de aceptación con empresarios compara utilidad frente a un solo coach.

## Dependencias y handoff

E49 aporta la ficha y evidencia inicial; E44 aporta seguimiento de resultados.
E67 empaqueta estos contratos como capacidades internas para Codex y Claude.
E45 no declara una plataforma soportada hasta que E67/E68 califiquen una
instalación limpia.
