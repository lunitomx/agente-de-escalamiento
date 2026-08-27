---
epic_id: "E55"
title: "PRD — Onboarding multifuente y conciliación"
status: "active"
---

# PRD E55

## Usuario y problema

Un empresario llega con conversación, archivos y exportaciones desiguales. No
debe contestar nuevamente lo que ya entregó ni recibir una calificación que
parezca objetiva cuando los datos no son comparables.

## Resultado

ESCALA conserva hechos locales con procedencia, enseña primero un tablero de
evidencia sin score, pregunta sólo vacíos materiales y bloquea comparaciones
financieras o de entidades que no tengan definición compatible.

## Reglas de producto

1. Un hecho no equivale a una recomendación: conserva fuente, periodo,
   definición, fecha base, confianza y comparabilidad.
2. Un dato no comparable se muestra como tal; nunca se usa silenciosamente
   para un score, ratio o recomendación.
3. Las preguntas faltantes son una por vez y sólo después de leer evidencia
   autorizada.
4. Toda persistencia reside bajo `.escala/`; no se requieren APIs, OAuth ni
   una base central.
5. El tablero no decide: prepara una decisión que el empresario confirma.

## Medición de éxito

- Un caso con dos fuentes muestra cada dato y su procedencia.
- Un caso con gasto/cobro incompatibles no produce comparación ni score.
- Un hecho existente elimina su pregunta equivalente del siguiente paso.
- Un caso ambiguo termina en una pregunta o parking lot trazable, no en una
  inferencia.

## Entregas ya verificadas

- S55.1: `Fact` local con los campos de procedencia y comparabilidad.
- S55.2: `facts_dashboard` separa conocido/no comparable/pendiente y declara
  `score: null`.
