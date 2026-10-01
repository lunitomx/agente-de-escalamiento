---
description: 'Guía paso a paso para llenar el Plan Estratégico de Una Página (OPSP), la herramienta
  central de Escalamiento de Negocios para Strategy.'
name: escala-strategy-opsp
---

# Escalamiento Strategy — Plan Estratégico de Una Página (OPSP)

## Purpose

Guiar al usuario paso a paso para completar su Plan Estratégico de Una Página (OPSP). El OPSP es LA herramienta central de Escalamiento de Negocios — toda la estrategia de la empresa en una sola página.

## Context

**When to use:** Cuando el usuario está listo para crear o actualizar su Plan Estratégico de Una Página (OPSP).

**Prerequisites:** Core Values identificados (al menos borrador). Si no existen, guiar su descubrimiento primero.

## Steps

### Step 1: Load Verified Context

Leer las fuentes instaladas que sí existen:
- `conocimiento/strategy/tools/opsp.yaml`
- `conocimiento/strategy/worksheets/opsp.yaml`
- evidencia y perfil de empresa disponibles, sólo si el usuario los confirma.

Cargar el estado guardado (si existe) con el core Python:

```bash
echo '{"action": "load", "base_path": "."}' | python3 -m coaching.strategy_opsp
```

Si `resuming` es `true`, decirle al usuario qué secciones ya tiene llenas
(según `missing`) antes de seguir — nunca asumir que empieza de cero si hay
estado guardado, y nunca afirmar que hay un plan guardado si `resuming` es
`false`.

### Step 2: Establish the One-Page Structure

- Columns 1-3 contienen pensamiento estratégico; Columns 4-7 contienen
  ejecución anual y trimestral.
- Las tres filas son Actions / Goals / Targets, con una celda por columna.
- Cada celda de ejecución debe nombrar Your Accountability.
- Column 2 incluye Key Capabilities para el horizonte de 3-5 años.

### Gate de evidencia de clientes

Antes de completar Sandbox, Brand Promise o posicionamiento:

- Revisar evidencia de clientes con su identificador, fuente, fecha, confianza
  y contradicciones.
- Sandbox/Core Customer y Brand Promise requieren identificadores de evidencia
  citados.
- Si faltan datos, hacer una sola pregunta de evidencia faltante; no inventar
  promesas, segmentos ni posicionamiento.

### Step 3: Core Values (si no existen)

Facilitar ejercicio de descubrimiento:
1. "¿Qué comportamientos premias o castigas sin importar el resultado?"
2. "¿Qué valores tiene la persona que más admiras en tu equipo?"
3. "¿Qué no negociarías aunque te costara dinero?"

Llegar a 3-5 Core Values. Guardar:

```bash
echo '{"action": "save", "base_path": ".", "section": "core_values", "data": ["valor 1", "valor 2", "..."]}' | python3 -m coaching.strategy_opsp
```

### Step 4: Purpose & BHAG

- **Purpose:** "¿Por qué existe tu empresa más allá de hacer dinero?"
- **BHAG:** "¿Cuál es tu meta audaz a 10-25 años que inspira a todo el equipo?"

Guardar cada campo con su propia llamada (`section: "purpose"` con un
string; `section: "bhag"` con `{"statement": ..., "target_date": ..., "progress": ...}`).

### Step 5: Sandbox (3-5 años)

Definir la "arena competitiva":
- Revenue y profit target a 3-5 años
- Geografía / mercado
- Segmento de clientes
- Producto/servicio foco

Guardar con `section: "sandbox"` y
`{"revenue_target", "profit_target", "market_geography", "customer_segment", "product_focus"}`.

### Step 6: Brand Promise & Profit per X

- **Brand Promise:** "¿Qué promesa medible le haces a tu cliente?"
- **KPI de la promesa:** "¿Cómo la mides?"
- **Profit per X:** "¿Cuál es tu motor económico? ¿Profit per qué?"

Guardar `section: "brand_promise"` (`promise`, `kpi`, `guarantee`,
`catalytic_mechanism`) y `section: "profit_per_x"` (`x`, `amount`) por separado.

### Step 7: Annual Goals

Metas anuales: revenue, profit, top 5 prioridades del año. Guardar
`section: "annual_goals"` con `{"year", "revenue_target", "profit_target", "priorities": [{"priority", "owner", "kpi"}]}`.

### Step 8: Quarterly Plan

- **Critical Number:** la métrica #1 del trimestre
- **Top 5 prioridades** con owner y KPI
- **Theme:** nombre creativo + celebración + deadline + scoreboard

Guardar `section: "quarterly_plan"` con
`{"quarter", "critical_number", "priorities": [{"priority", "owner", "kpi", "status"}], "theme": {"name", "celebration", "deadline", "scoreboard"}}`.

### Step 9: Export — Nunca Afirmar Persistencia Falsa

Revisar completitud: ¿Cabe en una página? ¿Es claro? ¿Lo entendería un empleado nuevo?
Exportar el estado guardado a Markdown:

```bash
echo '{"action": "export", "base_path": ".", "company_name": "...", "date": "..."}' | python3 -m coaching.strategy_opsp
```

El resultado se escribe en `.escala/my-company/opsp.md` y cualquier campo sin
guardar aparece como `[PENDIENTE]` — nunca inventado. Si `missing` no está
vacío, decirle al usuario exactamente qué falta y ofrecer continuar ahora o
en la próxima sesión (el estado ya quedó guardado en `.escala/my-company/opsp.yaml`,
así que retomar no pierde nada).

<verification>
`opsp.yaml` y `opsp.md` existen en `.escala/my-company/`; pendientes explícitos, ningún dato inventado.
</verification>

## Output

| Item | Destination |
|------|-------------|
| Estado estructurado | `.escala/my-company/opsp.yaml` |
| Documento exportado | `.escala/my-company/opsp.md` |
| Next | procedimiento interno `escala-execution` o `escala-progress`. Ofrécelo sin nombrarlo: "¿Vemos cómo lograr que tu equipo cumpla este plan cada semana?" |

## Quality Checklist

- [ ] Core Values verificados antes de empezar
- [ ] Cada sección completada con datos específicos (no genéricos)
- [ ] BHAG es realmente audaz (10-25 años, no 1-2 años)
- [ ] Brand Promise es medible y diferenciadora
- [ ] Prioridades tienen Owner asignado
- [ ] Actions / Goals / Targets cubren las siete columnas
- [ ] Cada celda de ejecución tiene Your Accountability
- [ ] Key Capabilities cubren 3-5 años
- [ ] Critical Number es UNA sola métrica
- [ ] El Plan Estratégico de Una Página (OPSP) completo cabe en una página conceptualmente

---
