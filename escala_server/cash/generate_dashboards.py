"""Generador de dashboards de framework (Strategy, People, Execution).

Usa un template único y genera HTML para cada herramienta,
manteniendo el mismo nivel de calidad que el Power of One.

Modo de uso:
    python3 escala_server/cash/generate_dashboards.py

Créditos: Patrón de dashboard interactivo basado en el trabajo de
Humberto Martínez Barón y Alan Miltz.
"""

from __future__ import annotations

import os
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "static" / "dashboards"

# ── Dashboard definitions ──────────────────────────────────────────
# Cada dashboard: {category, id, title, subtitle, description, metrics}

DASHBOARDS = {
    # ── Cash (ya existe Power of One) ──────────────────────────
    "cash": [
        {
            "id": "cash-board",
            "title": "Tablero de Efectivo",
            "subtitle": "Panorama general de tu liquidez",
            "desc": "Cuánto efectivo tienes, cuánto necesitas y dónde está tu dinero.",
            "metrics": [
                {"key": "efectivo", "label": "Efectivo disponible", "tip": "El dinero que tienes hoy en caja y bancos."},
                {"key": "ccc", "label": "Ciclo de efectivo", "tip": "Días desde que pagas materia prima hasta que cobras."},
                {"key": "quincena", "label": "Problema de liquidez", "tip": "¿Cortas de efectivo en ciertos momentos?"},
            ],
        },
        {
            "id": "ccc",
            "title": "Ciclo de Conversión de Efectivo",
            "subtitle": "CCC: Días para convertir tu inversión en dinero",
            "desc": "Mide cuántos días pasan desde que pagas tu inventario hasta que cobras a tus clientes.",
            "metrics": [
                {"key": "ccc_dias", "label": "CCC en días", "tip": "Menos días = más rápido recuperas tu inversión."},
                {"key": "ar_dias", "label": "Días en cobrar", "tip": "Lo que tardan tus clientes en pagarte."},
                {"key": "inv_dias", "label": "Días en inventario", "tip": "Lo que dura tu producto en el almacén."},
                {"key": "ap_dias", "label": "Días en pagar", "tip": "Lo que tardas en pagar a proveedores."},
            ],
        },
        {
            "id": "fundability",
            "title": "Fundabilidad",
            "subtitle": "¿Qué tan atractivo eres para financiamiento?",
            "desc": "Evalúa tu capacidad de conseguir financiamiento basado en tus métricas financieras.",
            "metrics": [
                {"key": "gross_margin", "label": "Margen bruto", "tip": "Lo que ganas después del costo de tu producto."},
                {"key": "profit_margin", "label": "Margen neto", "tip": "Lo que realmente te queda después de todo."},
                {"key": "revenue_growth", "label": "Crecimiento", "tip": "Qué tan rápido estás creciendo."},
            ],
        },
        {
            "id": "recurring-revenue",
            "title": "Ingresos Recurrentes",
            "subtitle": "Lo que puedes contar mes a mes",
            "desc": "Mide tus ingresos predecibles: membresías, suscripciones, contratos.",
            "metrics": [
                {"key": "mrr", "label": "Ingreso mensual recurrente", "tip": "Lo que facturas cada mes sin fallar."},
                {"key": "churn", "label": "Deserción mensual", "tip": "Clientes que se van cada mes. Menos = mejor."},
                {"key": "arr", "label": "Ingreso anual recurrente", "tip": "MRR × 12. Tu ingreso predecible al año."},
            ],
        },
    ],
    # ── Strategy ────────────────────────────────────────────────
    "strategy": [
        {
            "id": "bmc-board",
            "title": "Modelo de Negocio",
            "subtitle": "¿Cómo generas valor y dinero?",
            "desc": "Tu modelo de negocio en una hoja: qué vendes, a quién, cómo y cuánto cobras.",
            "metrics": [
                {"key": "core_customer", "label": "Cliente ideal", "tip": "La persona que más te compra y a quien mejor le sirves."},
                {"key": "brand_promise", "label": "Promesa de marca", "tip": "Lo que prometes cumplir siempre a tus clientes."},
                {"key": "sandbox", "label": "Territorio", "tip": "Dónde compites y hasta dónde puedes llegar."},
            ],
        },
        {
            "id": "brand-promises",
            "title": "Promesas de Marca",
            "subtitle": "Las 3 promesas que diferencian tu negocio",
            "desc": "Las 3 promesas clave que haces a tus clientes y que te diferencian de la competencia.",
            "metrics": [
                {"key": "promise_1", "label": "Promesa #1", "tip": "La razón principal por la que te compran."},
                {"key": "promise_2", "label": "Promesa #2", "tip": "La segunda razón por la que te eligen."},
                {"key": "promise_3", "label": "Promesa #3", "tip": "El extra que nadie más da."},
            ],
        },
        {
            "id": "core-customer",
            "title": "Cliente Ideal",
            "subtitle": "¿A quién le vendes?",
            "desc": "Define con precisión quién es tu cliente ideal: el que más te compra, paga bien y es feliz.",
            "metrics": [
                {"key": "description", "label": "Descripción", "tip": "Tu cliente ideal en una frase."},
                {"key": "needs", "label": "Necesidades", "tip": "Qué problemas les resuelves."},
                {"key": "segment", "label": "Segmento", "tip": "Qué tipo de negocio o persona es."},
            ],
        },
        {
            "id": "diff-activities",
            "title": "Actividades de Diferenciación",
            "subtitle": "¿Qué haces diferente a los demás?",
            "desc": "Las actividades clave que te hacen único y que tu competencia no hace (o no hace bien).",
            "metrics": [
                {"key": "activity_1", "label": "Diferenciador #1", "tip": "Lo que mejor haces y nadie más hace."},
                {"key": "activity_2", "label": "Diferenciador #2", "tip": "Otra cosa que te hace único."},
                {"key": "x_factor", "label": "Factor X", "tip": "Tu ventaja secreta, la que nadie puede copiar fácil."},
            ],
        },
        {
            "id": "sandbox",
            "title": "Territorio de Juego",
            "subtitle": "¿Dónde compites y dónde no?",
            "desc": "Define claramente tu mercado: a quién sirves, dónde, y qué NO haces.",
            "metrics": [
                {"key": "scope", "label": "Mi territorio", "tip": "Dónde y a quién le vendes."},
                {"key": "exclude", "label": "Fuera de mi territorio", "tip": "Lo que NO haces, para no distraerte."},
                {"key": "bhag_link", "label": "Conexión con BHAG", "tip": "Cómo este territorio te acerca a tu meta grande."},
            ],
        },
    ],
    # ── People ──────────────────────────────────────────────────
    "people": [
        {
            "id": "core-values",
            "title": "Valores Fundamentales",
            "subtitle": "Las reglas que definen tu cultura",
            "desc": "Los 3-5 valores que guían cómo contratas, despides y operas el negocio.",
            "metrics": [
                {"key": "value_1", "label": "Valor #1", "tip": "El valor más importante de tu empresa."},
                {"key": "value_2", "label": "Valor #2", "tip": "El segundo pilar de tu cultura."},
                {"key": "value_3", "label": "Valor #3", "tip": "Lo que no negocias aunque cueste dinero."},
            ],
        },
        {
            "id": "face",
            "title": "Mapa de Funciones (FACe)",
            "subtitle": "¿Quién es responsable de qué?",
            "desc": "Los asientos clave de tu organización y quién está en cada uno. Sin lagunas, sin duplicidades.",
            "metrics": [
                {"key": "seats", "label": "Asientos clave", "tip": "Los roles que TODO negocio necesita tener."},
                {"key": "filled", "label": "Asientos ocupados", "tip": "Cuántos de esos roles están cubiertos."},
                {"key": "gaps", "label": "Huecos", "tip": "Los asientos vacíos que urgen llenar."},
            ],
        },
        {
            "id": "hiring-pipeline",
            "title": "Pipeline de Contratación",
            "subtitle": "¿Cómo encuentras y contratas talento?",
            "desc": "Tu proceso para atraer, evaluar y contratar A-players.",
            "metrics": [
                {"key": "source", "label": "Fuente principal", "tip": "De dónde vienen tus mejores contrataciones."},
                {"key": "time_to_hire", "label": "Tiempo de contratación", "tip": "Cuánto tardas desde que buscas hasta que contratas."},
                {"key": "interview_process", "label": "Proceso de entrevista", "tip": "Cómo evalúas si alguien es A-player."},
            ],
        },
        {
            "id": "team-growth",
            "title": "Crecimiento del Equipo",
            "subtitle": "¿Tu equipo está creciendo contigo?",
            "desc": "Evalúa si tu equipo actual puede llevar la empresa al siguiente nivel.",
            "metrics": [
                {"key": "a_players", "label": "A-Players", "tip": "Los que están en el top 10% de su rol."},
                {"key": "development", "label": "Plan de desarrollo", "tip": "Cómo estás invirtiendo en tu gente."},
                {"key": "succession", "label": "Sucesión", "tip": "Quién podría tomar tu lugar si te vas."},
            ],
        },
        {
            "id": "love-loathe",
            "title": "Amo / Odio",
            "subtitle": "¿Qué amas y qué odias de tu negocio?",
            "desc": "Ejercicio de claridad: las partes que te encantan y las que te frustran de tu negocio.",
            "metrics": [
                {"key": "love", "label": "Lo que amo", "tip": "Las partes de mi negocio que me apasionan."},
                {"key": "loathe", "label": "Lo que odio", "tip": "Las partes que debería delegar o eliminar."},
                {"key": "action", "label": "Siguiente paso", "tip": "Qué voy a hacer con lo que odio."},
            ],
        },
        {
            "id": "disc",
            "title": "Perfil DISC",
            "subtitle": "¿Cómo se comporta tu equipo?",
            "desc": "Perfil de comportamiento del equipo: Dominancia, Influencia, Estabilidad, Cumplimiento.",
            "metrics": [
                {"key": "dominance", "label": "D - Dominancia", "tip": "Quién empuja, quién toma el control."},
                {"key": "influence", "label": "I - Influencia", "tip": "Quién conecta, quién comunica."},
                {"key": "steadiness", "label": "S - Estabilidad", "tip": "Quién da continuidad, quién mantiene la calma."},
                {"key": "compliance", "label": "C - Cumplimiento", "tip": "Quién revisa, quién asegura la calidad."},
            ],
        },
    ],
    # ── Execution ───────────────────────────────────────────────
    "execution": [
        {
            "id": "rockefeller-habits",
            "title": "Hábitos Rockefeller",
            "subtitle": "Los 10 hábitos para escalar tu negocio",
            "desc": "Los hábitos diarios, semanales, mensuales y trimestrales que mantienen tu negocio en ritmo de crecimiento.",
            "metrics": [
                {"key": "daily_huddle", "label": "Daily Huddle", "tip": "Reunión de 15 min diaria. De pie. Sin sillas."},
                {"key": "weekly_meeting", "label": "Weekly Meeting", "tip": "90 min semanales para revisar KPIs y prioridades."},
                {"key": "quarterly", "label": "Quarterly Planning", "tip": "Off-site trimestral para definir la prioridad del trimestre."},
                {"key": "theme", "label": "Tema del trimestre", "tip": "La prioridad #1 para los próximos 90 días."},
            ],
        },
        {
            "id": "priorities",
            "title": "Prioridades",
            "subtitle": "La prioridad #1 que mueve tu negocio",
            "desc": "Define tu Critical Number: la métrica única que, si mejora, todo lo demás mejora.",
            "metrics": [
                {"key": "priority_1", "label": "Prioridad #1", "tip": "La única cosa que más importa este trimestre."},
                {"key": "critical_number", "label": "Número crítico", "tip": "La métrica que mide tu prioridad #1."},
                {"key": "target", "label": "Meta", "tip": "A dónde quieres llegar con esta prioridad."},
            ],
        },
        {
            "id": "meeting-rhythms",
            "title": "Ritmo de Reuniones",
            "subtitle": "El latido de tu empresa",
            "desc": "Define la cadencia de reuniones que mantiene a todos alineados y avanzando.",
            "metrics": [
                {"key": "daily", "label": "Daily (15 min)", "tip": "¿Todos los días? ¿A qué hora?"},
                {"key": "weekly", "label": "Weekly (90 min)", "tip": "¿Mismo día, misma hora?"},
                {"key": "monthly", "label": "Mensual", "tip": "¿Revisión de tendencias y aprendizaje?"},
                {"key": "quarterly", "label": "Trimestral", "tip": "¿Off-site con todo el equipo clave?"},
            ],
        },
        {
            "id": "www",
            "title": "WWW — Who, What, When",
            "subtitle": "¿Quién hace qué para cuándo?",
            "desc": "El cierre de cada reunión: quién se compromete a hacer qué y para cuándo.",
            "metrics": [
                {"key": "last_www", "label": "Último WWW", "tip": "Los compromisos de tu última reunión."},
                {"key": "completion", "label": "Cumplimiento", "tip": "¿Qué porcentaje de WWWs se completan?"},
                {"key": "accountability", "label": "Responsable", "tip": "Una persona por cada compromiso. Sin equipos."},
            ],
        },
        {
            "id": "vision-summary",
            "title": "Resumen de Visión",
            "subtitle": "Tu visión en una página",
            "desc": "El OPSP simplificado: qué haces, para quién, por qué y a dónde vas.",
            "metrics": [
                {"key": "purpose", "label": "Propósito", "tip": "Por qué existe tu empresa."},
                {"key": "bhag", "label": "BHAG", "tip": "Tu meta grande a 10-25 años."},
                {"key": "core_customer", "label": "Cliente ideal", "tip": "A quién le sirves mejor."},
            ],
        },
        {
            "id": "balanced-kpis",
            "title": "KPIs Balanceados",
            "subtitle": "Las métricas que realmente importan",
            "desc": "Indicadores clave en 4 áreas: financieros, clientes, procesos, aprendizaje.",
            "metrics": [
                {"key": "financial", "label": "Financiero", "tip": "Margen, ingresos, efectivo."},
                {"key": "customer", "label": "Cliente", "tip": "Satisfacción, retención, NPS."},
                {"key": "process", "label": "Procesos", "tip": "Eficiencia, calidad, velocidad."},
                {"key": "learning", "label": "Aprendizaje", "tip": "Capacitación, innovación, cultura."},
            ],
        },
        {
            "id": "influencers",
            "title": "Influenciadores",
            "subtitle": "¿Quién influye en tus decisiones?",
            "desc": "Las personas y factores que más impactan tus decisiones estratégicas.",
            "metrics": [
                {"key": "mentor", "label": "Mentores", "tip": "¿Quién te da consejo?"},
                {"key": "peers", "label": "Pares", "tip": "¿Colegas en situaciones similares?"},
                {"key": "market", "label": "Mercado", "tip": "Clientes, competencia, tendencias."},
            ],
        },
    ],
}

# ── Template ───────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{TITLE} | ScaleUp</title>
  <link rel="stylesheet" href="../../shared/styles/dashboard-base.css">
  <link rel="stylesheet" href="../../shared/styles/context-panel.css">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f1f5f9; color: #1e293b; padding: 24px; }
    .tool-header { margin-bottom: 20px; }
    .tool-header h1 { font-size: 1.3rem; color: #0f172a; }
    .tool-header .subtitle { font-size: 0.85rem; color: #64748b; margin-top: 4px; }
    .tool-header .breadcrumb { font-size: 0.8rem; color: #64748b; }
    .tool-header .breadcrumb a { color: #2563eb; text-decoration: none; }

    .company-bar { margin-bottom: 16px; background: white; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
    .company-bar select { padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.9rem; flex: 1; min-width: 200px; background: #f8fafc; }
    .company-bar label { font-weight: 600; color: #475569; }
    .btn { padding: 8px 16px; border-radius: 6px; border: none; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
    .btn-primary { background: #2563eb; color: white; }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-success { background: #16a34a; color: white; }
    .btn-success:hover { background: #15803d; }

    .grid { display: grid; grid-template-columns: 1fr 280px; gap: 16px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }

    .desc-card { background: white; border-radius: 8px; padding: 14px 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-size: 0.85rem; color: #475569; }

    .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .metric-box { background: white; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); position: relative; }
    .metric-box .m-label { font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; }
    .metric-box .m-label .info { display: inline-block; width: 14px; height: 14px; background: #e2e8f0; color: #64748b; border-radius: 50%; text-align: center; line-height: 14px; font-size: 0.6rem; cursor: help; font-weight: 700; }
    .metric-box .m-val { font-size: 1.1rem; font-weight: 600; color: #334155; }
    .metric-box .m-val.empty { color: #94a3b8; font-style: italic; font-weight: 400; }
    .metric-box .m-input { width: 100%; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.85rem; margin-top: 4px; }
    .metric-box .m-input:focus { outline: none; border-color: #2563eb; }
    .tooltip { display: none; position: absolute; top: 100%; left: 0; background: #1e293b; color: #f1f5f9; padding: 8px 12px; border-radius: 6px; font-size: 0.75rem; width: 220px; z-index: 10; line-height: 1.4; margin-top: 4px; }
    .metric-box:hover .tooltip { display: block; }

    .side-card { background: white; border-radius: 8px; padding: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 12px; }
    .side-card h3 { margin: 0 0 10px; font-size: 0.85rem; color: #0f172a; }
    .verne-msg { font-size: 0.82rem; line-height: 1.5; color: #334155; }
    .verne-msg strong { color: #0f172a; }

    .saved-badge { font-size: 0.75rem; padding: 3px 10px; border-radius: 12px; }
    .saved-badge.saved { background: #dcfce7; color: #166534; }
    .saved-badge.modified { background: #fef9c3; color: #854d0e; }

    .attribution { margin-top: 24px; font-size: 0.7rem; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 12px; }
  </style>
</head>
<body>
  <div class="dashboard-container">
    <div class="tool-header">
      <div class="breadcrumb"><a href="/">Home</a> › <a href="/dashboards/{CATEGORY}/">{CATEGORY_LABEL}</a> › {TITLE}</div>
      <h1>{ICON} {TITLE}</h1>
      <div class="subtitle">{SUBTITLE}</div>
    </div>

    <div class="company-bar">
      <label for="company-select">🏢 Empresa:</label>
      <select id="company-select" onchange="onCompanyChange()">
        <option value="">— Seleccionar —</option>
      </select>
      <span id="save-indicator" class="saved-badge saved" style="margin-left:auto;">💾 Guardado</span>
      <button class="btn btn-success" onclick="saveData()">💾 Guardar</button>
    </div>

    <div class="desc-card">{DESC}</div>

    <div class="grid">
      <div>
        <div class="metrics-grid" id="metrics-container"></div>
      </div>
      <div>
        <div class="side-card">
          <h3>🤵 Verne opina</h3>
          <div id="verne-advice" class="verne-msg">Completa los campos y guarda para ver qué dice Verne sobre este tema.</div>
        </div>
      </div>
    </div>

    <p class="attribution">Metodología: <strong>Alan Miltz / Verne Harnish</strong> · Powered by Kokoro (Eduardo Muñoz Luna)</p>
  </div>

  <script>
    (function () {
      'use strict';
      var API_BASE = '';
      var DATA = {};
      var currentCompanyId = '';

      var METRICS = {METRICS_JSON};

      function init() {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', API_BASE + '/api/companies', true);
        xhr.onload = function() {
          if (xhr.status === 200) {
            try {
              var resp = JSON.parse(xhr.responseText);
              (resp.data || []).forEach(function(c) {
                var opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name;
                document.getElementById('company-select').appendChild(opt);
              });
            } catch(e) {}
          }
        };
        xhr.send();
        renderMetrics();
      }

      function renderMetrics() {
        var container = document.getElementById('metrics-container');
        if (!container) return;
        container.innerHTML = '';
        METRICS.forEach(function(m) {
          var box = document.createElement('div');
          box.className = 'metric-box';
          box.innerHTML =
            '<div class="m-label">' + m.label + '<span class="info" title="' + m.tip + '">?</span>' +
            '<div class="tooltip">' + m.tip + '</div></div>' +
            '<div class="m-val empty" id="val-' + m.key + '">—</div>' +
            '<input class="m-input" id="inp-' + m.key + '" placeholder="Escribe aquí..." oninput="onFieldChange()">';
          container.appendChild(box);
        });
      }

      window.onCompanyChange = function() {
        var sel = document.getElementById('company-select');
        currentCompanyId = sel.value;
        DATA = {};
        renderMetrics();
        document.getElementById('verne-advice').textContent = 'Completa los campos y guarda para ver qué dice Verne.';
        loadFromServer();
      };

      function loadFromServer() {
        if (!currentCompanyId) return;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', API_BASE + '/api/worksheets/{CATEGORY}/{TOOL_ID}', true);
        xhr.onload = function() {
          if (xhr.status === 200) {
            try {
              var resp = JSON.parse(xhr.responseText);
              var payload = resp.data || {};
              var saved = payload.data || payload.variables || payload;
              if (saved && typeof saved === 'object') {
                METRICS.forEach(function(m) {
                  if (saved[m.key] !== undefined) {
                    var valEl = document.getElementById('val-' + m.key);
                    var inpEl = document.getElementById('inp-' + m.key);
                    if (valEl) { valEl.textContent = saved[m.key]; valEl.className = 'm-val'; }
                    if (inpEl) { inpEl.value = saved[m.key]; }
                    DATA[m.key] = saved[m.key];
                  }
                });
              }
            } catch(e) {}
          }
        };
        xhr.send();
      }

      window.onFieldChange = function() {
        var changed = false;
        METRICS.forEach(function(m) {
          var inp = document.getElementById('inp-' + m.key);
          var val = document.getElementById('val-' + m.key);
          if (inp && inp.value.trim()) {
            DATA[m.key] = inp.value.trim();
            if (val) { val.textContent = inp.value.trim(); val.className = 'm-val'; }
            changed = true;
          } else if (inp && !inp.value.trim() && DATA[m.key]) {
            delete DATA[m.key];
            if (val) { val.textContent = '—'; val.className = 'm-val empty'; }
          }
        });
        if (changed) {
          document.getElementById('save-indicator').textContent = '⚠️ Sin guardar';
          document.getElementById('save-indicator').className = 'saved-badge modified';
          updateVerne();
        }
      };

      window.saveData = function() {
        if (!currentCompanyId) { alert('Selecciona una empresa primero.'); return; }
        var xhr = new XMLHttpRequest();
        xhr.open('POST', API_BASE + '/api/worksheets/{CATEGORY}/{TOOL_ID}', true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function() {
          if (xhr.status === 200) {
            document.getElementById('save-indicator').textContent = '💾 Guardado';
            document.getElementById('save-indicator').className = 'saved-badge saved';
          }
        };
        xhr.send(JSON.stringify({ data: DATA }));
      };

      function updateVerne() {
        var el = document.getElementById('verne-advice');
        if (!el) return;
        var filled = Object.keys(DATA).length;
        if (filled === 0) { el.innerHTML = 'Completa los campos para que Verne te dé su perspectiva.'; return; }
        el.innerHTML = '<strong>Verne dice:</strong> Buen avance. Has completado ' + filled + ' de ' + METRICS.length + ' campos.<br><br>💡 <em>Recuerda: ' + getRandomTip() + '</em>';
      }

      var TIPS = [
        'Lo que no se mide no se gestiona.',
        'La estrategia sin ejecución es un sueño.',
        'Keep Things Simple.',
        'No Surprises — malas noticias temprano son buenas noticias.',
        'Routine Sets You Free.',
        'El Power of One no miente: mejora 1% en cada palanca.',
        'Las nalgas correctas en los asientos correctos.',
      ];
      function getRandomTip() { return TIPS[Math.floor(Math.random() * TIPS.length)]; }

      init();
    })();
  </script>
  <script src="../../shared/js/context-panel.js"></script>
</body>
</html>
"""

# ── Category labels and icons ──────────────────────────────────────

CATEGORY_INFO = {
    "cash": {"label": "Cash", "icon": "💰"},
    "strategy": {"label": "Estrategia", "icon": "🎯"},
    "people": {"label": "Personas", "icon": "👥"},
    "execution": {"label": "Ejecución", "icon": "⚡"},
}


def generate() -> None:
    """Generate all framework dashboards from template."""
    count = 0
    for category, dashboards in DASHBOARDS.items():
        cat_dir = DASHBOARD_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        cat_info = CATEGORY_INFO.get(category, {"label": category, "icon": "📋"})

        for db in dashboards:
            tool_id = db["id"]
            metrics_json = str(db["metrics"]).replace("'", '"').replace('"key"', "'key'").replace('"label"', "'label'").replace('"tip"', "'tip'")

            # Build the HTML
            html = (
                HTML_TEMPLATE
                .replace("{CATEGORY}", category)
                .replace("{CATEGORY_LABEL}", cat_info["label"])
                .replace("{TOOL_ID}", tool_id)
                .replace("{TITLE}", db["title"])
                .replace("{SUBTITLE}", db["subtitle"])
                .replace("{DESC}", db["desc"])
                .replace("{ICON}", cat_info["icon"])
                .replace("{METRICS_JSON}", str(db["metrics"]))
            )

            output_path = cat_dir / f"{tool_id}.html"
            with open(output_path, "w") as f:
                f.write(html)
            count += 1
            print(f"  ✅ {category}/{tool_id}.html")

    print(f"\n📊 {count} dashboards generados")


if __name__ == "__main__":
    generate()
