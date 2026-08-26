# Retrospectiva — E27 Diagnóstico Narrativo con Evidencia

**Cierre:** 2026-08-26

## Cambio de producto

El diagnóstico deja de exigir una respuesta 1–5. Ahora escucha cuatro
descripciones —People, Strategy, Execution y Cash— y después propone una
calificación provisional con razones. La persona puede aceptarla, cambiarla,
dar un número directamente o dejarla sin calificación.

## Entregado

- Intake que separa nombre, giro, URL, logo/adjunto y texto libre.
- Caso RAISE: el nombre, el logo y el enlace no se confunden.
- Entrevista narrativa de una pregunta por vez con ejemplo, impacto y bloqueo.
- Síntesis visible antes de cualquier score.
- Notas confirmadas locales y compatibilidad con la ruta numérica anterior.
- Límites de fuentes externos: URL declarada no implica navegación, ingestión ni
  indexación.

## Evidencia

- tests/test_scaleup_conversation.py
- tests/test_scaleup_installer.py
- tests/test_connected_guidance.py
- tests/test_board.py

Todos los gates relevantes pasan de forma secuencial.
