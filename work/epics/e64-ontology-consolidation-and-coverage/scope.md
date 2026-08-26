---
epic_id: E64
title: Consolidación ontológica y release de cobertura
status: planned
depends_on: [E59, E60, E61, E62, E63]
---

# Scope E64

## Objetivo

Promover únicamente conocimiento aprobado de las cinco pasadas a una versión canónica coherente y publicable internamente, con una matriz de cobertura que pruebe qué unidad fuente llega a qué nodo.

## Dentro

- Normalización canónica sin borrar evidencia ni conflictos.
- Consolidación de aliases, referencias externas y relaciones tipadas.
- Validadores de huérfanos, enlaces rotos, herramientas sin decisión, reglas sin evidencia y métricas sin unidad/definición.
- Matriz `source_id → node_id → status`, reportes de cobertura/fidelidad y release interno.
- Revisión de estructuras mínimas: 4D, decisiones, barreras, disciplinas, hábitos, estratos, palancas, ritmos y campos de herramientas.

## Fuera

- Crear procedimientos o cambiar el catálogo de E56.
- Ocultar ambigüedad para mejorar indicadores de cobertura.
- Distribuir material derivado fuera de la frontera de E57/E36.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S64.1 Normalización | Nodos canónicos con mapa de aliases/evidencias. |
| 2 | S64.2 Integridad | Gates automatizados contra relaciones inválidas. |
| 3 | S64.3 Cobertura | Matriz fuente→nodo con exclusiones. |
| 4 | S64.4 Fidelidad | Reporte y bloqueo de críticos. |

## Criterios de terminación

- Todas las estructuras nombradas están representadas o justificadamente excluidas.
- Cero nodo/relación roto u huérfano.
- Cero distorsión crítica abierta.
- Todo concepto apto para compilación tiene procedencia y estado de revisión.

## Handoff y riesgos

E65 sólo consume esta release. No se acepta una salida "verde" si la cola de revisión contiene hallazgos críticos.
