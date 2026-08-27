---
epic_id: E63
title: Corpus Cash verificado
status: in_progress
depends_on: [E58]
related: [E55]
---

# Scope E63

## Objetivo

Hacer auditable el conocimiento Cash: fórmulas, unidades, supuestos, señales, herramientas y advertencias; nunca confundir metodología con evidencia financiera real de una empresa.

## Dentro

- Inventario de CCC, aceleración de efectivo, palancas financieras, rentabilidad y formularios.
- Extracción de fórmulas con unidad, periodo, inputs, salidas, condiciones y evidencia.
- Revisión adversarial de cifras, pasos, ejemplos y warnings.
- Puente tipado a E55 para exigir comparabilidad antes de calcular o recomendar.
- Matriz de cobertura/fidelidad y cola de ambigüedad.

## Fuera

- Conectar bancos, contabilidad, Drive u OAuth.
- Inventar flujo, margen, cobro, periodo fiscal o equivalencia entre métricas.
- Implementar dashboards o procedimientos; corresponde a E69 y épicas de producto ya existentes.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S63.1 Inventario | Unidades Cash clasificadas. |
| 2 | S63.2 Fórmulas/unidades | Schemas y fixtures de uso válido/inválido. |
| 3 | S63.3 Auditoría | Diferencias de fuente versus candidato resueltas o en review queue. |
| 4 | S63.4 Integración E55 | Reglas que bloquean datos no comparables. |
| 5 | S63.5 Cobertura exhaustiva | Cada unidad se mapea con evidencia, como fuente especial o con handoff explícito. |

## Criterios de terminación

- 100% de fórmulas y prescripciones con evidencia.
- Ningún cálculo aceptado sin unidad, periodo e inputs declarados.
- Comparaciones incompatibles quedan bloqueadas o marcadas como no comparables.
- Cero hallazgo crítico de fidelidad pendiente.

## Estado de evidencia

- S63.1, S63.3 y S63.5 tienen borradores privados trazables; los candidatos siguen sin promoción canónica hasta revisión independiente.
- S63.2 conserva como candidato la fórmula de Working Capital Days respaldada directamente por `u0320`; el multiplicador literal y su semántica se mantienen sin normalizar hasta revisión independiente.
- CASh no compila fórmulas hasta revisar la fuente externa citada por el libro; unidad, periodo y comparabilidad siguen siendo contratos E38/E55. La e-Form oficial pública v20/03 sólo confirma semánticamente la estructura de CASh y Power of One. La decisión de licencia/uso y sus rutas están listas en `source-authorization-request.md`; no se presume autorización por la ficha pública.

## Handoff y riesgos

Entrega a E64 y E69. No sustituye la conciliación multifuente ni permite que un output financiero se vuelva consejo profesional definitivo.
