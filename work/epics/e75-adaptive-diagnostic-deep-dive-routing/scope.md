---
epic_id: E75
title: Diagnóstico adaptativo, confirmación y routing a Deep Dives
status: in_progress
depends_on: [E49, E55]
blocked_handoffs: [E65]
related: [E71, E72, E73]
---

# Scope E75

## Objetivo

Convertir el output provisional de E49 en una conversación de confirmación y
selección de trabajo profundo: diagnóstico narrativo primero, scoring explicable
después, elección humana y solicitud progresiva de evidencia.

## Dentro

- Modelo de assessment con comprensión de empresa, señales, evidencia, unknown,
  hipótesis, N/A, confianza, freshness, score opcional y objeción del usuario.
- Guion conversacional “esto entendí / esto no sé / esto parece ser el reto /
  ¿lo ves igual?”.
- Explicación de por qué se proponen como máximo dos Deep Dives y qué evidencia
  adicional pide cada uno.
- Handoff tipado a Cash Learning Day, research/market, People, Execution o
  dashboard advisor, sin prellenar datos no confirmados.
- Sugerencias de revisión/automatización con propuesta de frecuencia, valor,
  datos usados y aceptación/rechazo/diferir.
- Tests de cambio de foco, score insuficiente, conflicto con el usuario y
  retención de corrección.

## Fuera

- Un test fijo de 1–5 como base principal de diagnóstico.
- Obligar al usuario a seguir el orden editorial de una metodología.
- Ejecutar Deep Dive, research o dashboard sin confirmación del foco.
- Exponer la complejidad de los cuatro especialistas al usuario.

## Dependencias y secuencia

```text
E49 two-speed diagnostic + E55 facts
                       ↓
S75.1 contract → S75.2 confirmación
                       ↓
                   E65 procedures
                       ↓
S75.3 elección → S75.4 handoff → S75.5 sugerencias → S75.6 evals
```

S75.1 y S75.2 no necesitan E65: corrigen el intake y producen un assessment
narrativo confirmable. S75.3–S75.5 sí esperan procedimientos verificados de
E65; hasta entonces el sistema no promete ni ejecuta un Deep Dive inexistente.
E71/E72/E73 son destinos de handoff; E45 decide si un caso transversal requiere
más de un especialista, pero el usuario recibe una sola ruta ejecutiva.

## Criterios de terminación

- La pantalla/salida inicial muestra comprensión y evidencia antes que número.
- Un score sin evidencia suficiente se reemplaza por cobertura/desconocidos,
  no por cero ni una apariencia de precisión.
- El usuario puede corregir o elegir un foco distinto y el sistema conserva la
  corrección con procedencia.
- La primera solicitud de datos detallados ocurre después de seleccionar Deep
  Dive, salvo información mínima indispensable.
- Las sugerencias de automatización no se ejecutan sin aceptación explícita.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Assessment demasiado largo | límite de síntesis y rutas, no recapitulación completa. |
| Puntaje vuelve a dominar la conversación | evidencia/objeción aparecen primero; score es secundario. |
| Usuario elige ruta equivocada | permite cambiar/posponer y declara trade-off. |
| Automatización invasiva | propuesta explícita, aceptación y opción de pausar. |
