---
epic_id: "E38"
title: "Cash and Financial Intelligence"
status: "in_progress"
created: "2026-07-22"
mission: "escala-local-v2-plan-maestro-2607202112"
---

# Epic Brief: E38 — Cash and Financial Intelligence

## Hypothesis

Si ESCALA puede leer los workbooks reales del empresario, explicar qué
estructura encontró, separar hechos de inferencias y pedir aclaraciones antes
de calcular, entonces puede convertir datos financieros imperfectos en una
vista útil de la salud de la empresa sin obligar al dueño a migrar sus hojas a
una plantilla nueva.

La confianza depende de que cada cifra conserve procedencia hasta hoja/celda o
rango, que las limitaciones sean visibles y que una recomendación de cash no
se presente cuando faltan datos o los supuestos no están confirmados.

## Success Metrics

- **Leading:** workbooks CSV/XLSX existentes se perfilan por hojas, tablas,
  fórmulas, periodos, monedas y unidades; los mapeos ambiguos generan
  preguntas concretas y no valores inventados.
- **Lagging:** una empresa sintética recibe P&L, balance, flujo de efectivo,
  CCC, Power-of-One y escenarios únicamente cuando los datos permiten
  derivarlos, con trazabilidad y un reporte visual local descargable.

## Appetite

L — 4 historias. Es la primera capa financiera consumible por el empresario;
no convierte todavía la salida en diagnóstico 0–100, estrategia, reuniones ni
instalador empaquetado.

## Rabbit Holes / Explicit Rejections

- No usar APIs de Google Drive/OneDrive, OAuth, SaaS, base de datos cloud,
  worker hospedado ni telemetría.
- No reconstruir cifras faltantes por intuición ni tratar una inferencia como
  un hecho confirmado.
- No imponer formato contable ni sobrescribir el workbook del empresario.
- No prometer análisis universal de Excel, OCR o asesoría fiscal/legal; cada
  proveedor y límite se declara explícitamente.
