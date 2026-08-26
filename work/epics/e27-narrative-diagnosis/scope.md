# Epic Scope: E27 — Diagnóstico Narrativo con Evidencia

**Status:** Complete — 2026-08-26
**Dependencies:** E22 (memoria), E23 (contexto humano), E25 (guía de fuentes)
**Tamaño:** XL

## Outcome

Reemplazar el primer tramo obligatorio de respuestas 1–5 por una entrevista
narrativa progresiva que produzca hechos, evidencia y, únicamente cuando aporte
valor, una propuesta de puntuación confirmable.

## In scope

- Intención de intake que separa nombre, giro, URL, adjunto y texto libre.
- Reconocimiento explícito de enlaces/archivos como fuentes, sin confundirlos
  con la actividad de la empresa.
- Preguntas narrativas adaptativas para People, Strategy, Execution y Cash.
- Captura de ejemplo, impacto, práctica actual, bloqueo y responsable.
- Síntesis por decisión y confirmación/edición de lo entendido.
- Puntuación sugerida y explicada; aceptar, modificar u omitir.
- Compatibilidad con diagnóstico y plan existentes, migración de estado y
  pruebas de reanudación.
- Persistencia local de hechos y resúmenes consentidos; límites E25 para
  contenido externo o sensible.

## Out of scope

- Navegar, descargar, indexar o compartir automáticamente URLs/adjuntos.
- Obligar la puntuación numérica.
- Inferir hechos no declarados a partir de un logo, nombre o URL.
- Cambiar el One Page Plan salvo para consumir la síntesis confirmada.

## Acceptance criteria

- [x] Una respuesta detallada nunca se rechaza por no incluir 1–5.
- [x] Logo, enlace y actividad de negocio quedan en campos diferenciados.
- [x] Cada decisión termina con una síntesis que la persona confirma o corrige.
- [x] Toda puntuación propuesta muestra sus razones y puede omitirse.
- [x] La ruta corta sigue funcionando para quien quiera dar un número.
- [x] El flujo se reanuda localmente sin duplicar hechos ni perder material.
- [x] Los casos de RAISE y de una empresa sin enlaces pasan de punta a punta.

## Historias

| Orden | Story | Resultado |
|:---:|---|---|
| 1 | S27.1 — Intake con fuentes diferenciadas | Nombre, giro, URL, adjunto y texto no se confunden. |
| 2 | S27.2 — Entrevista narrativa adaptativa | Preguntas de valor, ejemplo, impacto y bloqueo. |
| 3 | S27.3 — Síntesis y puntuación explicable | Resumen confirmable; score opcional y justificable. |
| 4 | S27.4 — Memoria, migración y privacidad | Estado reanudable; hechos locales y frontera E25. |
| 5 | S27.5 — Evaluación conversacional | Dorados, adversariales, RAISE y regresiones. |
