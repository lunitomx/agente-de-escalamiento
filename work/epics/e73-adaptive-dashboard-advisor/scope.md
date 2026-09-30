---
epic_id: E73
title: Asesor adaptativo de dashboards de negocio
status: planned
jira_key: "ESCALA-37"
depends_on: [E38, E40, E55, E65, E67, E80]
---

# Scope E73

## Coordinación correctiva — 2026-09-12

[E80](../e80-evidence-backed-diagnostics-document-intake/scope.md) posee la
reparación del dashboard actual y el contrato que separa completitud, evidencia
y desempeño. E73 consume ese contrato al recomendar/generar nuevos paneles;
no vuelve a implementar scores ni retrasa la corrección de placeholders H04.

## Objetivo

Recomendar y, tras aceptación, generar dashboards locales que respondan una
pregunta ejecutiva concreta usando únicamente métricas con procedencia,
definición, periodo y suficiente cobertura.

## Dentro

- Modelo de `DashboardRecommendation` con decisión, audiencia, frecuencia,
  owner, métricas, fuentes, freshness, visual, campos faltantes y estado.
- Reglas de priorización: impacto, urgencia, cobertura, accionabilidad y
  redundancia frente a dashboards existentes.
- Patrones por decisión: Cash (caja mínima/forecast/CCC/margen), Execution
  (Rocks/compromisos/ritmo), People (accountability/capacidad con límites),
  Strategy (cliente/mercado/customer journey/hipótesis).
- Especificación local y generación aprobada de artifacts HTML/CSV/Markdown,
  conectados al recibo de datos y a la siguiente revisión.
- Explicación honesta de datos faltantes, métricas no comparables o visuales no
  recomendados.

## Fuera

- Dashboard cloud, colaboración en tiempo real, OAuth o visualización de datos
  que el usuario no autorizó persistir.
- Sugerir más de dos paneles simultáneamente sin que el usuario lo pida.
- Crear métricas de People sensibles sin contrato/consentimiento específico.
- Recalcular finanzas: Cash Learning Day/E38 siguen siendo la autoridad.

## Dependencias y secuencia

```text
E38/E40/E55 datos y decisiones + E65 procedimientos + E67 cuatro perfiles
                                  ↓
S73.1 contrato → S73.2 recomendación → S73.3 feasibility
                                      ↓
                          S73.4 artifacto + S73.5 catálogo → S73.6 evals
```

E72 entrega especificaciones financieras; E71 entrega market/customer journey;
E75 puede recomendar cuál dashboard solicitar después de un deep dive.

## Criterios de terminación

- Toda propuesta señala la decisión y la métrica/cobertura que la soporta.
- Datos stale, ambiguos o faltantes producen una explicación y una pregunta,
  no un gráfico de precisión falsa.
- El empresario puede aceptar, rechazar o diferir cada propuesta; el sistema
  recuerda esa decisión sin insistir cada sesión.
- Los cuatro patrones se generan localmente y respetan privacidad/roles.
- Pruebas demuestran no redundancia, no sobrescritura y artefactos redacted.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Paneles decorativos | requerir decisión, owner y cadencia antes de generar. |
| Exceso de recomendaciones | límite de dos y ranking por evidencia/impacto. |
| Confundir dato débil con insight | gate de procedencia, freshness y comparabilidad. |
