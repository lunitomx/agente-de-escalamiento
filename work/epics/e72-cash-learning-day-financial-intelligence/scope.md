---
epic_id: E72
title: Learning Day de Cash e inteligencia financiera guiada
status: planned
depends_on: [E38, E55, E63, E65, E67]
---

# Scope E72

## Objetivo

Convertir la plantilla financiera v2 y los workbooks admitidos por E38 en una
facilitación de Cash progresiva, trazable y segura que produzca decisiones y no
sólo reportes.

## Dentro

- Adaptador de plantilla con cuatro hojas: resultados, balance, flujo de caja
  12M y razones financieras; detección de versión y capability report.
- Registro de campos de captura contra campos derivados/formulados, etiquetas de
  periodo y reglas de signos/unidad/moneda.
- Intake escalonado: contexto → P&L → balance → flujo mínimo → profundización
  por modelo → ratios y escenarios.
- Validación de balance, cobertura de data, actual/forecast, vencimiento,
  comparabilidad de métricas y “N/A por modelo”.
- Interpretación guiada de liquidez, caja mínima, margen, capital de trabajo,
  DSO, DIO, DPO y CCC cuando las precondiciones se cumplan.
- Paquete de decisión con evidencia, supuestos, preguntas, riesgo, KPI,
  responsable, Who/What/When y cadencia.
- Especificación de dashboard para E73 y archivo local/redacted sólo tras
  consentimiento de persistencia.

## Fuera

- Cambiar la plantilla o escribir en el workbook original.
- Asesoría fiscal/contable/legal, deuda recomendada o aprobación de pagos.
- Forzar a todos los modelos a reportar inventario, ingresos recurrentes o las
  mismas razones financieras.
- Reconciliar automáticamente movimientos que E55 clasificó como ambiguos.

## Dependencias y secuencia

```text
E38 comprensión de workbooks + E55 conciliación + E63 conocimiento Cash
                         ↓
                 S72.1 mapping/contrato
                         ↓
S72.2 intake → S72.3 validación → S72.4 Learning Day → S72.5 decisión
                                                  ↓
                                  S72.6 consentimiento → S72.7 evaluación
```

E65 aporta contrato de procedimiento; E67 instala `cash-analyst`; E73 consume
la especificación de dashboard, no vuelve a calcular finanzas.

## Criterios de terminación

- La plantilla se reconoce sin sobrescribirla y expone qué campos faltan.
- Un balance que no cuadra bloquea interpretación y produce preguntas útiles.
- Cada ratio/cálculo lleva periodo, unidad, fórmula/método, inputs y estado de
  comparabilidad; las métricas no aplicables no penalizan el diagnóstico.
- Flujo de efectivo distingue ventas, facturas, cobranza y efectivo.
- Sólo hechos y artefactos autorizados se persisten; el archivo original no se
  versiona ni se sube por ESCALA.
- Los cinco tipos de caso de S72.7 pasan su evaluación y el empresario puede
  elegir profundizar o detenerse con un resultado honesto.

## Riesgos y guardrails

| Riesgo | Mitigación |
|---|---|
| Presión por llenar todo el Excel | insight temprano + campos opcionales/N-A por modelo. |
| Dato contable tratado como caja | tipos explícitos y validación E55 antes de cálculo. |
| Falsa seguridad de un ratio | precondiciones, rango/contexto y evidencia en pantalla. |
| Fuga de estados financieros | consentimiento por nivel, redacción y almacenamiento local. |
