# Epic Scope: E30 — Lectura Inteligente de Documentos del Negocio

**Status:** Draft
**Dependencies:** E28 (pyyaml disponible)
**Tamaño:** M (4 historias, ~6h)
**Origen:** Visión de coach — el agente no debe ser ciego. El empresario ya tiene sus datos en algún lado.

## Visión

"Pásame tu balance, tu organigrama, tu pipeline de ventas — yo lo leo." El empresario no quiere re-escribir sus datos en worksheets. Ya los tiene en Excel, Google Sheets, PDFs, CSVs. Escala debe leer lo que le den, en el formato que sea, y traducirlo a las herramientas Scaling Up.

No pre-cableamos integraciones (no sabemos qué CRM usa cada quien). Creamos skills que guían al usuario a exportar lo suyo y el agente lo procesa.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S30.1 — Skill: Lectura de organigrama → FACe** | M | El usuario sube su organigrama (Excel, Sheets, PDF, foto). Escala extrae nombres, roles, jerarquía. Detecta huecos vs FACe ideal. Sugiere: "Te falta VP de Ventas y tu Controller está overloaded con 12 reportes." |
| **S30.2 — Skill: Lectura financiera → Power of One + CCC** | M | El usuario sube su P&L y balance (PDF, Excel, foto). Escala extrae ingresos, costos, márgenes, cuentas por cobrar/pagar, inventario. Calcula Power of One y CCC automáticamente. Dice: "Mejorando 1% cada palanca, tu cash aumenta $X." |
| **S30.3 — Skill: Lectura de pipeline → Scorecard de ventas** | S | El usuario exporta su pipeline a CSV desde cualquier CRM. Escala lee: deals activos, valor, etapa, velocidad. Calcula métricas clave y las cruza con Prioridad #1. "Tu pipeline tiene $500K pero 60% está estancado en propuesta hace 30+ días." |
| **S30.4 — Ingreso rápido: foto de pizarrón** | S | El usuario toma foto de su pizarrón del daily huddle. Escala extrae WWWs, KPIs, obstáculos. Los ingiere a memoria/. "Capturé 3 WWWs, 2 obstáculos. ¿Asigno responsables?" |

## Done Criteria

- [ ] S30.1: subir organigrama → FACe poblado con huecos detectados
- [ ] S30.2: subir P&L → Power of One calculado automáticamente
- [ ] S30.3: subir CSV de pipeline → scorecard con alertas
- [ ] S30.4: foto de pizarrón → WWWs ingeridos en memoria/
