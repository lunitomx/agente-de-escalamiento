---
epic_id: E61
title: Corpus Strategy verificado
status: in_progress
depends_on: [E58]
---

# Scope E61

## Objetivo

Construir la representación trazable de Strategy para que el agente pueda distinguir una pregunta de core, enfoque, diferenciación, visión o ejecución estratégica antes de prescribir una herramienta.

## Dentro

- Inventario de conceptos, preguntas, acciones, warnings, métricas y formularios de Strategy.
- Extracción y auditoría independientes de SWT, siete estratos, Vision Summary, OPSP, cliente/nicho, promesas y diferenciadores.
- Relaciones tipadas entre mindshare, cliente, promesas, garantía, estrategia, actividades, X-factor, Profit per X y horizontes.
- Validación visual/semántica de los formularios y sus campos dependientes.
- Matriz de cobertura y reporte de distorsiones.

## Fuera

- Decidir la estrategia de una empresa sin evidencia local.
- Compilar el OPSP o siete estratos a procedimientos de usuario; eso es E65/E69.
- Usar datos de mercado no autorizados o actualizar silenciosamente casos históricos.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S61.1 Inventario | Lista de unidades y tipos contra E57. |
| 2 | S61.2 Candidatos/revisión | Registro de aprobación, rechazo y ambigüedad. |
| 3 | S61.3 Relaciones | Grafo de dependencias con evidencia. |
| 4 | S61.4 Fidelidad de herramientas | Comparación de formulario, campos y condiciones. |
| 5 | S61.5 Cobertura exhaustiva | Cada unidad del rango queda mapeada con evidencia, como fuente especial o con handoff explícito. |

## Criterios de terminación

- Dominio clasificado por completo o exclusiones justificadas.
- Toda prescripción y relación obligatoria tiene evidencia.
- Cero relaciones inventadas, condiciones perdidas o conflictos críticos ocultos.
- Formularios validados antes de que E69 los vuelva procedimiento.

## Estado de evidencia

- S61.1, S61.2, S61.3 y S61.5 tienen borradores privados trazables; los candidatos siguen sin promoción canónica hasta revisión independiente.
- S61.4 tiene recibo semántico contra la e-Form oficial pública v20/03 para SWT, Seven Strata, OPSP y Vision Summary; sigue pendiente sólo la inspección visual del layout, no la disponibilidad de un activo fuente. El recibo privado se prepara con `../e60-people-corpus-fidelity/visual-layout-review-protocol.md`.

## Handoff y riesgos

Entrega a E64. E55 sigue siendo autoridad de datos de empresa; este corpus no convierte una hipótesis de cliente o mercado en un hecho.
