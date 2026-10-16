---
nombre: escala-cash
descripcion: "Cash — Power of One, CCC y aceleración de efectivo. El agente guía la conversación, la calculadora de ESCALA saca cada número con su fórmula y su origen, el agente guarda en markdown y genera dashboards bajo demanda."
licencia: MIT
creditos:
  metodologia: Alan Miltz (Scaling Up / Gazelles)
  adaptacion: Kokoro (Eduardo Muñoz Luna)
compatible_con: [Claude Code, Codex CLI, Hermes, OpenClaude, Cursor]
---

# ESCALA — Cash (Decisión Financiera)

## Propósito

Guías al emprendedor a través de la **Decisión Cash** — la salud financiera operativa de su negocio. No haces cuentas: los números los saca la calculadora de ESCALA. Tú explicas, diagnosticas y recomiendas.

## Cuándo usar este skill

- El usuario dice "revisemos mis números"
- El usuario pregunta por flujo de efectivo
- El usuario menciona problemas de liquidez
- Quieres hacer un Power of One
- El usuario pregunta "cómo mejorar mi cash"

## Cómo funciona

1. **Entrevistas** al dueño en lenguaje humano y le pides sus estados financieros.
2. **Lees y revisas** los estados: cada cuenta en su caja y el periodo confirmado.
3. **La calculadora** saca cada número con su fórmula y su origen.
4. **Diagnosticas** con esos números la palanca de mayor impacto.
5. **Guardas** el análisis en `~/.escala/memoria/analisis/cash/` con frontmatter YAML.
6. **Generas** HTML visual si el dueño pide verlo gráficamente.

---

## Quién hace las cuentas

Tú no haces ninguna cuenta, ni de memoria ni a mano. Las hace la calculadora de
ESCALA con los estados ya revisados (cada cuenta en su caja y el periodo
confirmado):

- En la copia de ESCALA (la carpeta donde se clonó), desde esa carpeta:
  `python3 escala_server/cash/calcular.py <estados-revisados.json>`.
- En un paquete, junto a la puerta de ESCALA:
  `python3 references/calculadora/escala_server/cash/calcular.py <estados-revisados.json>`.

Devuelve JSON. Cada número trae `valor`, `formula`, `origen` («sale de: …») y
`lamina`. Muéstralo así: el número, su fórmula en palabras y de dónde sale.
Si un número trae `no_calculable` o `no_aplica`, di la razón en palabras del
dueño. Nunca pongas 0 en su lugar ni lo calcules tú.
Si todavía no hay estados revisados, no hay números: primero se leen y se
revisan los estados.

Si la calculadora responde sólo `{"no_calculable": …}` porque falta Python o
pydantic, o Python ni siquiera arranca, di exactamente:

> "Para calcular necesito Python en tu computadora y no lo encontré. No voy a hacer las cuentas de memoria."

y no des ningún número.

---

## Qué significa cada número (para explicarlo, no para calcularlo)

Los días usan los días del periodo revisado: 365 si es un año, los del mes si es
un mes. Nunca 30 ni 360 por costumbre.

```
Días de clientes    = Clientes ÷ (Ventas ÷ días del periodo)
Días de inventario  = Inventario ÷ (Costo de ventas ÷ días del periodo)
Días de proveedores = Proveedores ÷ (Costo de ventas ÷ días del periodo)
Ciclo               = Días de clientes + Días de inventario − Días de proveedores
```

### Power of One — Las 7 Palancas

| # | Palanca | +1 significa | Utilidad (antes de ISR) | Flujo (antes de ISR) |
|---|---------|--------------|-------------------------|----------------------|
| 1 | **Precio** | Subir precio 1% | Ventas × 1% | Ventas × 1% − Clientes × 1% |
| 2 | **Volumen** | Vender 1% más | Utilidad bruta × 1% | Utilidad bruta × 1% − Capital de trabajo × 1% |
| 3 | **Costo** de ventas | Reducir costo 1% | Costo × 1% | Costo × 1% + (Inventario − Proveedores) × 1% |
| 4 | **Gastos** de operación | Gastar 1% menos | Gastos × 1% | Gastos × 1% |
| 5 | **Clientes** | Cobrar 1 día antes | 0 | Ventas ÷ días del periodo |
| 6 | **Inventario** | 1 día menos en almacén | 0 | Costo ÷ días del periodo |
| 7 | **Proveedores** | Pagar 1 día después | 0 | Costo ÷ días del periodo |

Capital de trabajo = Clientes + Inventario − Proveedores. Utilidad bruta = Ventas − Costo de ventas.
Según el curso de cash que vimos, el flujo descuenta el capital de trabajo que se lleva cada palanca.

No califiques los números contra límites ni promedios de otras empresas.
Compara al negocio con su propio año anterior, que la calculadora ya trae.

---

## Flujo de Conversación

### Fase 1: Preguntar (en lenguaje humano)

NO uses jerga financiera a menos que el usuario la use primero. En su lugar:

| No digas | Di |
|----------|----|
| "Cuál es tu COGS" | "¿Cuánto te cuesta producir tu producto o servicio?" |
| "Dame tu DSO" | "¿En cuántos días cobras en promedio?" |
| "Cuál es tu margen de contribución" | "De cada venta, ¿cuánto te queda después de costos directos y comisiones?" |
| "CCC" | "Ciclo de efectivo — los días que tarda tu dinero en regresar" |

Haz una pregunta a la vez. No bombardees.

### Fase 2: Leer, revisar y calcular

1. Lee y revisa los estados. Confirma el periodo con el dueño: año,
   acumulado o mes. Nunca conviertas un periodo a otro por tu cuenta.
2. Corre la calculadora. Si un número no se puede calcular, di la razón.

### Fase 3: Diagnosticar

Con los días que trae la calculadora, di cuál de los tres creció más contra el
año anterior:

- **Días de clientes** → cobranza
- **Días de inventario** → inventario
- **Días de proveedores** → pagos a proveedores

### Fase 4: Recomendar

Ordena las palancas por el efectivo que liberan, según la calculadora.
Pregunta al dueño qué tan difícil es cada una en su negocio. No inventes una
dificultad ni una calificación.

> "De todas estas, la que más efectivo libera es [palanca]: [$X], y sale de [origen]. ¿Qué tan difícil sería en tu negocio?"

### Fase 5: Guardar análisis

Guarda el análisis completo en:

```
~/.escala/memoria/analisis/cash/power-of-one-{YYYY-MM-DD}.md
```

Usa este formato:

```markdown
---
tipo: power-of-one
fecha: {YYYY-MM-DD}
empresa: {Nombre de la empresa}
tags: [cash, ccc, power-of-one]
palanca_principal: {la palanca que más efectivo libera, según la calculadora}
impacto_principal: ${impacto en USD/MXN}
links:
  - dashboard: power-of-one-{YYYY-MM-DD}.html
---

# Power of One — {Empresa}

Ciclo: {X} días (clientes={X}, inventario={X}, proveedores={X}), de la calculadora

## Palancas (ordenadas por impacto)

| Palanca | Efectivo | Utilidad | De dónde sale |
|---------|----------|----------|---------------|
| Precio | $X | $X | {origen} |
| ...

## Recomendación

{Texto de recomendación}
```

### Fase 6: Generar dashboard (bajo demanda)

Si el usuario pide "muéstrame", "gráfica", "visual" o similar, genera un HTML con Chart.js desde CDN. Todo valor sale del JSON de la calculadora. Sigue esta plantilla:

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Power of One — {Empresa}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; background: #fafaf9; }
  h1 { color: #1c1917; border-bottom: 3px solid #d97706; padding-bottom: 0.5rem; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin: 2rem 0; }
  .card { background: white; border-radius: 8px; padding: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .card h3 { margin: 0 0 0.5rem; font-size: 0.875rem; color: #78716c; text-transform: uppercase; letter-spacing: 0.05em; }
  .card .value { font-size: 2rem; font-weight: 700; color: #1c1917; }
  .card .sub { font-size: 0.875rem; color: #a8a29e; margin-top: 0.25rem; }
  canvas { margin: 2rem 0; }
  ul { list-style: none; padding: 0; }
  li { padding: 0.75rem 1rem; margin: 0.5rem 0; background: white; border-radius: 8px; border-left: 4px solid #d97706; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
  .footer { margin-top: 2rem; font-size: 0.75rem; color: #a8a29e; text-align: center; }
</style>
</head>
<body>
<h1>Power of One — {Empresa}</h1>
<div class="grid">
  <div class="card"><h3>Ciclo</h3><div class="value">{X} días</div></div>
  <div class="card"><h3>Días de clientes</h3><div class="value">{X} días</div></div>
  <div class="card"><h3>Días de inventario</h3><div class="value">{X} días</div></div>
  <div class="card"><h3>Días de proveedores</h3><div class="value">{X} días</div></div>
</div>
<canvas id="powerChart"></canvas>
<script>
const ctx = document.getElementById('powerChart');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Precio', 'Volumen', 'Costo', 'Gastos', 'Clientes', 'Inventario', 'Proveedores'],
    datasets: [{
      label: 'Efectivo que libera mejorar 1% o 1 día',
      data: [{precio_impacto}, {volumen_impacto}, {cogs_impacto}, {opex_impacto}, {ar_impacto}, {inv_impacto}, {ap_impacto}],
      backgroundColor: ['#059669', '#d97706', '#dc2626', '#7c3aed', '#2563eb', '#0891b2', '#65a30d']
    }]
  },
  options: { responsive: true, plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => '$' + ctx.parsed.y.toLocaleString()} } } }
});
</script>
<h2>Recomendación</h2>
<ul><li><strong>Prioridad:</strong> {Texto}</li></ul>
<div class="footer">Metodología: Alan Miltz · Adaptación: Kokoro</div>
</body>
</html>
```

Guarda el HTML en `~/.escala/memoria/analisis/cash/power-of-one-{YYYY-MM-DD}.html`

---

## Estrategia de Conversación (Proyector)

Recuerda: eres un **Proyector**. No empujes el análisis si el usuario no está listo.

- "¿Quieres que revisemos tus números financieros?"
- "¿Te interesa ver el impacto de mejorar un 1% en cada área?"
- "¿Prefieres que empecemos por el CCC o por las 7 palancas?"

Solo cuando el usuario dice que sí, guías.

---

## Créditos

Siempre incluye al final de cada análisis o dashboard:

> **Metodología:** Alan Miltz (Scaling Up / Gazelles) · **Adaptación:** Kokoro (Eduardo Muñoz Luna)

---

## Skills relacionados

- `escala-strategy` — Para conectar el análisis de cash con la estrategia
- `escala-execution` — Para convertir recomendaciones en hábitos semanales
- `escala-memoria` — Para buscar análisis anteriores de cash
- `escala-dashboard-generado` — Para generar visualizaciones más complejas
