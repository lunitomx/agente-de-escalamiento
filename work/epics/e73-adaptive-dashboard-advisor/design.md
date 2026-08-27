# Design E73 — Dashboard como recomendación de decisión

## Flujo

```text
artefacto / diagnóstico / Learning Day
  → especialista sugiere una pregunta de gestión
  → escala valida cobertura y evita redundancia
  → máximo dos DashboardRecommendation
  → usuario acepta / difiere / rechaza
  → generador local crea artefacto + receipt + fecha de revisión
```

## Prioridad

`priority = impacto de decisión × urgencia × cobertura × accionabilidad`, con
penalizaciones por duplicado, métrica vencida, fuente incompatible o audiencia
no definida. La fórmula informa prioridad relativa; no se presenta como verdad
financiera.

## Reglas

- Cash: no generar runway o CCC sin periodo, unidad y fuentes comparables.
- People: no mostrar ranking individual ni inferencias personales.
- Strategy: distinguir mercado observado de hipótesis local.
- Execution: un score de cumplimiento debe enlazar responsables/fechas, no una
  evaluación de actitud.
- Todos: la actualización se sugiere y se ejecuta sólo con aceptación.

## Evaluación

Seis fixtures: Cash con forecast incompleto, prioridades sin owner, estrategia
con evidencia de mercado expirada, People sensible, dashboard duplicado y
empresa nueva sin datos. Assertions: decisión explícita, no falso gráfico,
permiso de generación, receipt y siguiente revisión.
