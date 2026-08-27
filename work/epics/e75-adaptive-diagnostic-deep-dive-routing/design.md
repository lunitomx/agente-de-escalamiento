# Design E75 — De comprensión a Deep Dive elegido

## Secuencia de experiencia

```text
Welcome / evidencia existente
 → “Esto entendí de tu empresa”
 → señales + desconocidos + assessment explicable
 → “¿Lo ves igual? ¿Qué corregirías?”
 → máximo dos rutas propuestas
 → usuario elige / cambia / difiere
 → procedimiento específico pide evidencia detallada
 → artifacto + owner + KPI + cadencia
```

## Contrato

`NarrativeAssessment` contiene cuatro capas que nunca se mezclan:

1. `company_confirmed`: hechos aprobados por la empresa.
2. `evidence_observed`: respuestas/archivos con fuente, periodo y freshness.
3. `interpretation`: hipótesis del agente con confianza y contraevidencia.
4. `user_position`: acuerdo, corrección, desacuerdo o foco elegido.

El `score` sólo aparece si su cobertura supera un umbral declarado por decisión.
Incluye denominador, items N/A y evidencia soporte. No se deriva de silencios.

## Routing

- Cash: Cash Learning Day E72 cuando existen señales de liquidez, margen,
  cobranza, forecast o el usuario lo elige.
- Strategy: E71 cuando necesita mercado, competencia, ICP o customer journey.
- Execution/People: procedimiento validado de E65/E69 y perfiles E45.
- Dashboard: E73 sólo cuando hay pregunta de decisión y datos suficientes.

## Evaluación

Fixtures: fundador con respuestas abiertas ricas, empresa sin datos financieros,
usuario que desacuerda con Cash, modelo de servicio con N/A de inventario y
usuario que rechaza una automatización. Assertions: no Likert-wall, evidencia
primero, cambio persistente, mínimo de datos y ningún side effect sin permiso.
