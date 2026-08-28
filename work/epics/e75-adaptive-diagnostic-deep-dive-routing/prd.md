---
epic_id: E75
title: Diagnóstico adaptativo, confirmación y routing a Deep Dives
status: in_progress
depends_on: [E49, E55]
blocked_handoffs: [E65]
related: [E71, E72, E73]
---

# PRD E75 — Diagnóstico adaptativo, confirmación y routing a Deep Dives

## Problema

El usuario no quiere un cuestionario rígido ni que una escala numérica sustituya
la comprensión de su negocio. Tras una conversación inicial, necesita verse
reflejado en un diagnóstico provisional, corregirlo y elegir dónde profundizar:
Cash, estrategia/mercado, personas, ejecución o su próximo Learning Day.

## Usuario y trabajo por resolver

Un empresario termina el Welcome y pregunta: “¿qué entendiste de mi empresa?,
¿cuál es mi reto real y qué hacemos ahora?”. Debe recibir una respuesta
argumentada y editable, no una sentencia automática.

## Resultado de producto

ESCALA resume oferta, modelo, evidencia, desconocidos y señales de las cuatro
decisiones. Entrega un assessment narrativo con puntaje secundario sólo si hay
cobertura suficiente: evidencia, confianza, razones, N/A y preguntas que
cambiarían la lectura. El usuario confirma/corrige y elige un Deep Dive. La
rutina pide entonces la evidencia detallada del dominio, no antes.

## Principios

- Respuestas abiertas y evidencia concreta preceden a cualquier puntuación.
- Un número es una señal explicable, nunca la totalidad del diagnóstico.
- El usuario puede objetar el enfoque y proponer otro; la objeción se conserva.
- El sistema profundiza en una prioridad a la vez, salvo razón explícita para
  una intervención transversal.
- Las automatizaciones/revisiones se sugieren; el usuario acepta frecuencia y
  alcance antes de activarlas.

## Historias

| ID | Historia | Resultado |
|---|---|---|
| S75.1 | Contrato de assessment narrativo | Comprensión, evidencia, incertidumbre, puntaje secundario y objeción quedan tipados. |
| S75.2 | Conversación de confirmación | ESCALA devuelve “esto entendí” y permite corregir industria, oferta, cliente, modelo y reto. |
| S75.3 | Selección de Deep Dive | Propone máximo dos rutas, explica por qué y permite que el usuario elija. |
| S75.4 | Handoff progresivo | Cash, research/strategy, People o Execution reciben sólo la evidencia/datos que requieren. |
| S75.5 | Learning Day y sugerencias | Propone próximo Learning Day, dashboard o investigación; nada se agenda sin aceptación. |
| S75.6 | Evaluación | Casos de poca evidencia, N/A, desacuerdo del usuario, cambio de foco y datos sensibles pasan. |

## Entrega inicial autorizada

S75.1 y S75.2 se entregan antes de E65 porque sólo consumen los contratos
existentes de conversación, evidencia y consentimiento. La entrega reemplaza
el flujo público que exigía veinte respuestas 1–5 por una conversación abierta
con hallazgos, incógnitas y confirmación. No invoca ni simula los procedimientos
de profundidad: S75.3–S75.5 permanecen bloqueadas hasta que E65 los compile
desde nodos verificados.

## Métricas de éxito

- El usuario puede llegar a un primer insight sin llenar una matriz fija.
- Cada conclusión contiene por qué, con qué evidencia y qué podría cambiarla.
- La profundización pide datos materiales después de elegir foco.
- Cero rutas o automatizaciones se activan por una puntuación sin confirmación.

## Fuera

- Reemplazar E49 o reabrir su cierre; E75 es la siguiente experiencia sobre sus
  contratos.
- Quinta decisión o un score de personalidad/empleados.
- Programar notificaciones/automatizaciones externas sin aceptación.
