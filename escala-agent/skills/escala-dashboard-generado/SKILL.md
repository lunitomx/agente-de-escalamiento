---
description: "El agente genera HTML visual bajo demanda usando Chart.js desde CDN. No hay dashboards fijos — cada visualización nace cuando el usuario la pide."
license: MIT
name: escala-dashboard-generado
---

# Dashboard Generado — ESCALA

## Propósito

Cuando el usuario pide ver datos visualmente, el agente **genera un HTML**
con Chart.js (desde CDN) y lo abre en el navegador. No hay HTML fijo.
Cada dashboard es único, creado para ese momento, con esos datos.

## Cuándo generar un dashboard

| Si el usuario dice... | Genera... |
|-----------------------|-----------|
| "Muéstrame una gráfica de mis dailys" | Line chart: scores en el tiempo |
| "¿Cómo voy en Rockefeller Habits?" | Radar chart: cobertura de hábitos |
| "¿Cuánto impacto tiene cada palanca?" | Bar chart: Power of One por palanca |
| "Quiero ver un resumen general" | Dashboard 4D con semáforos |
| "Compárame esta semana vs la anterior" | Dual line chart o tabla comparativa |

## Template base

Siempre usa esta estructura. Solo cambia el `chartData` y el `type`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TÍTULO} | ESCALA</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
           background: #f1f5f9; color: #1e293b; padding: 24px; }
    h1 { font-size: 1.3rem; color: #0f172a; margin-bottom: 20px; }
    .chart-box { background: white; border-radius: 12px; padding: 20px; 
                 box-shadow: 0 1px 3px rgba(0,0,0,0.08); max-width: 700px; margin: 0 auto; }
    canvas { width: 100% !important; }
    .meta { text-align: center; font-size: 0.8rem; color: #94a3b8; margin-top: 12px; }
  </style>
</head>
<body>
  <h1>{TÍTULO}</h1>
  <div class="chart-box">
    <canvas id="chart"></canvas>
  </div>
  <div class="meta">Generado por ESCALA · {FECHA}</div>
  <script>
    const ctx = document.getElementById('chart').getContext('2d');
    new Chart(ctx, {
      type: '{TIPO}',  // 'line' | 'bar' | 'radar' | 'doughnut'
      data: {CHART_DATA},
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true } }
      }
    });
  </script>
</body>
</html>
```

## Tipos de gráfica y cuándo usarlas

### Line chart — tendencias en el tiempo
```javascript
// Datos: scores de dailys por fecha
type: 'line',
data: {
  labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
  datasets: [{
    label: 'Score Rockefeller',
    data: [6, 8, 10, 7, 9],
    borderColor: '#2563eb',
    backgroundColor: 'rgba(37,99,235,0.1)',
    fill: true,
    tension: 0.3
  }]
}
```

### Radar chart — cobertura de hábitos
```javascript
// Datos: qué elementos del daily se cubren
type: 'radar',
data: {
  labels: ['Logros', 'Prioridades', 'Obstáculos', 'Métricas', 'Prio #1'],
  datasets: [{
    label: 'Cobertura',
    data: [100, 100, 100, 0, 100],  // 100 = presente, 0 = ausente
    backgroundColor: 'rgba(22,163,74,0.2)',
    borderColor: '#16a34a'
  }]
}
```

### Bar chart — comparación de impactos
```javascript
// Datos: Power of One impacto por palanca
type: 'bar',
data: {
  labels: ['Precio', 'Volumen', 'COGS', 'Gastos', 'A/R', 'Inventario', 'A/P'],
  datasets: [{
    label: 'Impacto en Cash Flow',
    data: [120000, 48000, 38400, 21600, 41096, 19726, 19726],
    backgroundColor: ['#16a34a', '#2563eb', '#ca8a04', '#dc2626', '#8b5cf6', '#ec4899', '#14b8a6']
  }]
}
```

### Doughnut chart — composición
```javascript
// Datos: qué porcentaje del tiempo se cubre cada hábito
type: 'doughnut',
data: {
  labels: ['Cumplido', 'Faltante'],
  datasets: [{
    data: [80, 20],
    backgroundColor: ['#16a34a', '#e2e8f0']
  }]
}
```

## Dashboard 4D — Vista general

Cuando el usuario pide un resumen general, genera un HTML con 4 tarjetas
y Chart.js:

```html
<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:800px;margin:0 auto;">
  <div style="background:white;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08);">
    <h3>💰 Cash</h3>
    <div style="font-size:2rem;font-weight:700;color:{COLOR};">{CCC} días</div>
    <div style="font-size:0.8rem;color:#94a3b8;">Ciclo de efectivo</div>
  </div>
  <!-- Repite para Strategy, People, Execution -->
</div>
```

Colores de semáforo:
- ✅ Verde (`#16a34a`) = bueno (CCC < 30, score > 80%)
- ⚠️ Amarillo (`#ca8a04`) = regular
- ❌ Rojo (`#dc2626`) = malo (CCC > 60, score < 50%)

## Cómo guardar y abrir

1. Genera el HTML completo en una variable
2. Guárdalo en `~/.escala/memoria/dashboard/{nombre}.html`
3. Ábrelo con `open ~/.escala/memoria/dashboard/{nombre}.html` (macOS)
   o `xdg-open` (Linux)
4. Registra en el índice de memoria

```bash
# Guardar
cat > ~/.escala/memoria/dashboard/dailys-semana-2026-05-30.html << 'EOF'
... HTML generado ...
EOF

# Abrir (macOS)
open ~/.escala/memoria/dashboard/dailys-semana-2026-05-30.html

# Abrir (Linux)
xdg-open ~/.escala/memoria/dashboard/dailys-semana-2026-05-30.html
```

## Ejemplo completo

Usuario: "Muéstrame una gráfica de cómo van mis dailys esta semana"

1. Agente lee `memoria/dailys/` y encuentra:
   - 2026-05-26-score-6.md
   - 2026-05-27-score-8.md
   - 2026-05-28-score-10.md

2. Agente genera:
```html
<h1>📊 Tendencia de Dailys — Esta Semana</h1>
<div class="chart-box">
  <canvas id="chart"></canvas>
</div>
<script>
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Lun 26', 'Mar 27', 'Mié 28'],
      datasets: [{
        label: 'Score Rockefeller',
        data: [6, 8, 10],
        borderColor: '#16a34a',
        fill: true
      }]
    }
  });
</script>
```

3. Guarda en `memoria/dashboard/tendencia-dailys-2026-05-30.html`
4. Abre en el navegador
5. Responde: "Tus dailys van en aumento: 6 → 8 → 10. ¡Sigue así!"
