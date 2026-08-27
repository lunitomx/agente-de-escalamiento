# Design E72 — Learning Day de Cash

## Flujo conversacional

```text
Provisional focus Cash / selección del dueño
  → explica resultado y pide permiso para profundizar
  → confirma empresa, moneda, fecha de corte, responsable y modelo
  → muestra cobertura disponible y pide sólo el siguiente bloque material
  → valida balance y comparabilidad
  → analiza caja / forecast / ratios aplicables
  → devuelve foco, dashboard, plan 90 días y siguiente revisión
```

## Mapeo de la plantilla v2

| Bloque | Datos de captura | Derivados que ESCALA no pide editar |
|---|---|---|
| Resultados | ventas por línea, costos directos, gastos, impuestos | ventas/costos totales, utilidad y márgenes. |
| Balance | activos, A/R, inventarios, pasivos, deuda, capital | totales y control de balance. |
| Flujo 12M | caja inicial, entradas/salidas, inversión/financiamiento, caja mínima | flujo neto, caja final, déficit/excedente. |
| Razones | no requiere captura directa | liquidez, deuda, márgenes, DSO/DIO/DPO/CCC. |

## Reglas esenciales

- Datos a junio acumulados no se comparan con un año completo sin marcar factor
  de anualización o limitación.
- Servicios puros pueden omitir DIO; comercio/manufactura no deben inferirlo si
  falta inventario/costo comparable.
- `REVISAR` de balance antecede a cualquier consejo o dashboard de ratios.
- Caja mínima es un objetivo confirmado por la empresa, no una recomendación
  impuesta por ESCALA.
- Forecast se etiqueta por mes y por grado de certeza; no se mezcla con cierre
  histórico.

## Salidas estructuradas

`FinancialLearningDayState`, `FinancialFact`, `ValidationFinding`,
`CashDecisionPack` y `DashboardRecommendation`. Cada objeto guarda source,
periodo, unidad, sensibilidad, consentimiento y estado de revisión.

## Evaluación

Fixtures: servicios B2B sin inventario, comercio con inventario, manufactura,
flujo parcial de seis meses, balance que no cuadra y workbook con campos
conflictivos. Se revisan cálculo, preguntas, límites, redacción y no-mutación
del archivo original.
