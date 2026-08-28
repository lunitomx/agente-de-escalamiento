---
epic_id: E67
title: Capacidades internas y adaptadores portables
status: planned
depends_on: [E45, E65, E56]
---

# E67 — Capacidades internas y adaptadores portables

## Resultado

Los procedimientos del MVP se ejecutan detrás de `escala`, con núcleo común y adaptadores mínimos por plataforma; no aparecen como una nueva lista pública de skills.

## Historias

| ID | Historia | Termina cuando |
|---|---|---|
| S67.1 | Mapeo procedure→capability | `catalog.yaml` declara contrato, versión, evidencia y lifecycle de cada capacidad interna. |
| S67.2 | Adaptador Codex | La instalación publica sólo `escala` y conserva instrucciones específicas fuera del núcleo. |
| S67.3 | Adaptador Claude | La misma semántica y artefactos se obtienen sin copiar lógica de metodología. |
| S67.4 | Paridad y migración | Aliases conservan compatibilidad limitada y ninguna ruta duplica una implementación. |
| S67.5 | Paquete de especialistas | Los cuatro perfiles de E45 se generan desde núcleo común e instalan sus adaptadores sin crear nuevas puertas públicas. |
| S67.6 | Compatibilidad Agent Plugins v1 | El mismo núcleo se publica como paquete portable con manifest estándar, skills descubiertos en ubicación fija y extensiones aisladas. |

## Cierre

Una instalación limpia expone sólo `escala`; ambos adaptadores generan rutas y artefactos semánticamente equivalentes y el core no contiene instrucciones exclusivas de una plataforma.
