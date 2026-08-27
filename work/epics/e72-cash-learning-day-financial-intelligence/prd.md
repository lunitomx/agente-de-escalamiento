---
epic_id: E72
title: Learning Day de Cash e inteligencia financiera guiada
status: planned
depends_on: [E38, E55, E63, E65, E67]
owners: [cash-analyst, escala]
reference_template: Plantilla_Estados_Financieros_Cash_v2
---

# PRD E72 — Learning Day de Cash e inteligencia financiera guiada

## Problema

E38 ya puede perfilar workbooks y derivar análisis financiero cuando los datos
lo permiten. Falta la experiencia de facilitación: saber qué pedir, en qué orden
y con qué validación para conducir un Learning Day de Cash sin convertirlo en
un interrogatorio ni interpretar datos contables incompatibles.

## Usuario y trabajo por resolver

Un líder identifica Cash como foco o elige profundizar después del diagnóstico.
Quiere traer su Excel real o completar una plantilla, entender su posición de
caja y salir con un foco de 90 días, no con celdas llenas sin decisión.

## Resultado de producto

`escala` explica qué puede conseguir, pide consentimiento para leer/persistir y
activa `cash-analyst`. El facilitador usa la plantilla financiera v2 como
contrato de referencia: estado de resultados comparativo, balance comparativo,
flujo de 12 meses y razones financieras. Pide primero el mínimo necesario y
sólo profundiza donde detecte incertidumbre material.

La salida es un paquete de Cash:

- calidad/cobertura de datos, periodos, moneda, owner y supuestos;
- control de balance y discrepancias por resolver;
- posición de liquidez, forecast frente a caja mínima y meses de riesgo;
- márgenes, capital de trabajo, DSO/DIO/DPO/CCC sólo si aplican;
- dashboard local recomendado/generado cuando la cobertura lo soporte;
- un cuello de botella de Cash, dueño, KPI, Who/What/When y revisión.

## Principios

1. La plantilla guía la conversación pero no sustituye los libros reales ni
   obliga a una empresa de servicios a llenar inventario.
2. Cada importe distingue actual, estimado, forecast, reconocimiento contable,
   facturación, cobranza y movimiento de efectivo.
3. Nunca se pide editar una fórmula/total derivado: sólo se solicitan campos de
   captura y se preserva el Excel original.
4. Estados financieros y archivos adjuntos son sensibles: se leen en sesión;
   guardar archivo o hechos derivados requiere autorización explícita.
5. El resultado informa y facilita; no es asesoría fiscal, contable, de crédito
   o de inversión.

## Historias

| ID | Historia | Resultado |
|---|---|---|
| S72.1 | Contrato de plantilla y mapping | Hojas, campos editables, fórmulas derivadas, periodos y versiones quedan reconocibles. |
| S72.2 | Intake progresivo de Cash | Conversación pide datos por etapas y muestra cobertura antes de profundizar. |
| S72.3 | Validaciones financieras | Balance, signos, unidades, periodos, actual-vs-forecast y comparabilidad bloquean conclusiones inválidas. |
| S72.4 | Facilitación del Learning Day | Ruta por P&L, balance, flujo 12M, ratios y modelo aplicable. |
| S72.5 | Paquete de decisión y dashboards | Foco de Cash, plan 90 días y visuales locales sólo con evidencia suficiente. |
| S72.6 | Consentimiento y colaboración | Guardado autorizado, fuentes redacted y handoff al workspace compartido de E74. |
| S72.7 | Calificación | Empresa de servicios, comercio, manufactura, datos parciales y balance inválido pasan casos. |

## Métricas de éxito

- Ninguna conclusión de Cash se produce con balance inválido o métricas no
  comparables sin declararlo.
- El líder entiende qué falta y puede llegar a un primer insight antes de llenar
  todos los campos opcionales.
- Todo plan de Cash incluye baseline, owner, fecha y revisión.
- Cero modificaciones no autorizadas del Excel original o persistencia de
  importes sensibles sin consentimiento.

## Fuera

- Sustituir al contador, asesor fiscal o tesorería profesional.
- Conectar bancos, ERP, contabilidad, Drive u OAuth.
- Sincronizar SQLite o almacenar Excel en repositorios de producto.
- Pronósticos “inteligentes” sin supuestos y datos confirmados.
