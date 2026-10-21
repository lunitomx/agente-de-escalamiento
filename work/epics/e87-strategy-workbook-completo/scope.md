---
epic_id: E87
title: Strategy workbook completo — todas las herramientas del workbook, con guía, tips y vista visual
status: active
jira_key: "ESCALA-107"
created: 2026-10-20
source: metodologias que debes tener llenadas/EOA Strategy 2025 Participant Workbook (1).pdf
components_touched: conocimiento, escala-skills, coaching
change_mode: additive
---

# Scope E87

## Objetivo

Que ESCALA cubra todas las herramientas del workbook de Strategy (38 páginas), con una guía de llenado, tips profesionales y una vista visual al terminar cada una. Cierra la brecha que dejó E6 (prometió 34 hojas, cerró con 15).

## Decisiones del dueño (2026-10-20)

- Alcance: solo el workbook de Strategy. People, Execution y Cash quedan fuera.
- Se agregan las herramientas faltantes: BMC con puente a Scaling Up, Strategy Canvas, Vision Summary, Promesa de marca completa, preguntas del Cliente central, Actividades diferenciadoras, pronóstico de Caja de arena y los prompts de IA.
- Cada herramienta lleva guía de llenado, tips profesionales (investigación con `rai-research`) y, al terminar, una vista visual (artefacto de Claude o HTML) además de markdown/yaml.
- No copiar imágenes del workbook (derechos de Gazelles, p. 38). Las tarjetas citan número de página.
- Prueba de cobertura página por página obligatoria.

## Causa raíz que se evita

S6.3 (2026-04-20) pobló la ontología de Strategy desde 18 nodos escritos antes de leer el workbook. El criterio contó nodos, no cobertura. E6 prometió 34 hojas y cerró con 15. E87 exige que cada página del workbook mapee a una tarjeta o se marque como contenido que no es herramienta antes de diseñar historias.

## Criterios de terminado de la épica

- Prueba de cobertura: 38 de 38 páginas mapeadas a tarjeta de conocimiento o marcadas como no herramienta, en un archivo versionado.
- Cada herramienta nueva tiene guía de llenado, tips y vista visual, con prueba.
- Ninguna imagen del workbook en el repo.

## Historias (por diseñar)

Desglose tentativo. Se confirma en la fase de diseño, después de S87.1.

| Historia | Entrega | Estado |
|---|---|---|
| S87.1 | Inventario y prueba de cobertura página por página | por diseñar |
| S87.2 | BMC + puente BMC → Scaling Up | por diseñar |
| S87.3 | Strategy Canvas (una hoja que une cuatro piezas) | por diseñar |
| S87.4 | Promesa de marca completa (p. 16-21) | por diseñar |
| S87.5 | Cliente central y Actividades diferenciadoras (p. 20, 25) | por diseñar |
| S87.6 | Vision Summary (p. 7, 35, 36) | por diseñar |
| S87.7 | Vista visual al terminar el llenado | por diseñar |
| S87.8 | Tips profesionales investigados | por diseñar |

Los prompts de IA (p. 9, 16, 20, 26, 29, 33, 34) y el pronóstico de Caja de arena (p. 28) se asignan a las historias de arriba en el diseño.

## Fuera de alcance

- People, Execution y Cash del mismo workbook de origen.
- Reescribir el tablero `bmc-board.html` existente más allá de lo que el puente exija.
- Imágenes del workbook en el repo.

## Reglas heredadas

- Español llano, con ejemplo real en cada herramienta.
- Solo se versiona `work/epics/e87-strategy-workbook-completo/`.
