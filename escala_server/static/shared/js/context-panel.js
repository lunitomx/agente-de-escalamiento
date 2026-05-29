/**
 * ScaleUp Context Panel — Knowledge sidebar for dashboards
 *
 * Auto-detects dashboard category from URL path and fetches
 * relevant context from the knowledge graph API.
 *
 * Usage: include in any dashboard HTML:
 *   <link rel="stylesheet" href="../../shared/styles/context-panel.css">
 *   <script src="../../shared/js/context-panel.js"></script>
 */
(function () {
  'use strict';

  var CATEGORY_MAP = {
    cash: 'cash',
    ccc: 'cash',
    'power-of-one': 'cash',
    fundability: 'cash',
    'recurring-revenue': 'cash',
    strategy: 'strategy',
    'bmc-board': 'strategy',
    'brand-promises': 'strategy',
    'core-customer': 'strategy',
    'diff-activities': 'strategy',
    sandbox: 'strategy',
    people: 'people',
    'core-values': 'people',
    disc: 'people',
    face: 'people',
    'hiring-pipeline': 'people',
    'love-loathe': 'people',
    'team-growth': 'people',
    execution: 'execution',
    'balanced-kpis': 'execution',
    influencers: 'execution',
    'meeting-rhythms': 'execution',
    priorities: 'execution',
    'rockefeller-habits': 'execution',
    'vision-summary': 'execution',
    www: 'execution',
  };

  function detectCategory() {
    var path = window.location.pathname.toLowerCase();
    // Match /dashboards/{category}/ pattern
    var match = path.match(/\/dashboards\/(\w+)\//);
    if (match && CATEGORY_MAP[match[1]]) {
      return CATEGORY_MAP[match[1]];
    }
    // Fallback: try to detect from filename
    var filename = path.split('/').pop().replace('.html', '');
    if (CATEGORY_MAP[filename]) {
      return CATEGORY_MAP[filename];
    }
    return null;
  }

  function createPanel() {
    // Check if panel already exists
    if (document.getElementById('context-panel')) return;

    var panel = document.createElement('div');
    panel.id = 'context-panel';
    panel.className = 'collapsed'; // Start collapsed by default
    panel.innerHTML =
      '<div class="context-panel-header">' +
        '<h3>📘 Contexto de Scaling Up</h3>' +
        '<div class="context-category" id="context-category"></div>' +
      '</div>' +
      '<div class="context-panel-body" id="context-panel-body">' +
        '<div class="context-loading">Cargando contexto…</div>' +
      '</div>';

    var toggle = document.createElement('button');
    toggle.id = 'context-panel-toggle';
    toggle.className = 'context-panel-toggle';
    toggle.textContent = '📘';
    toggle.title = 'Abrir contexto de Scaling Up';
    toggle.addEventListener('click', function () {
      var isCollapsed = panel.classList.toggle('collapsed');
      toggle.textContent = isCollapsed ? '📘' : '✕';
      toggle.title = isCollapsed ? 'Abrir contexto' : 'Cerrar contexto';
    });

    document.body.appendChild(panel);
    document.body.appendChild(toggle);
  }

  function loadContext(category) {
    var bodyEl = document.getElementById('context-panel-body');
    var categoryEl = document.getElementById('context-category');
    if (!bodyEl) return;

    categoryEl.textContent = 'Categoría: ' + category.charAt(0).toUpperCase() + category.slice(1);

    var apiUrl = '/api/knowledge/context?category=' + encodeURIComponent(category);

    fetch(apiUrl)
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.status === 'error') {
          bodyEl.innerHTML = '<div class="context-error">Error: ' + (data.message || 'sin datos') + '</div>';
          return;
        }
        renderContext(data, bodyEl);
      })
      .catch(function (err) {
        bodyEl.innerHTML = '<div class="context-error">Error al cargar: ' + err.message + '</div>';
      });
  }

  function renderContext(data, container) {
    var html = '';

    // Principles section
    if (data.principles && data.principles.length > 0) {
      html += '<div class="context-section">';
      html += '<div class="context-section-title">📌 Principios</div>';
      data.principles.forEach(function (p) {
        var name = p.name || p.properties?.name || '—';
        var desc = p.properties?.description || '';
        html += '<div class="context-item"><div class="item-name">' + escapeHtml(name) + '</div>';
        if (desc) html += '<div class="item-desc">' + escapeHtml(desc) + '</div>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Habits section
    if (data.habits && data.habits.length > 0) {
      html += '<div class="context-section">';
      html += '<div class="context-section-title">🔄 Hábitos</div>';
      data.habits.forEach(function (h) {
        var name = h.name || h.properties?.name || '—';
        var desc = h.properties?.description || '';
        html += '<div class="context-item"><div class="item-name">' + escapeHtml(name) + '</div>';
        if (desc) html += '<div class="item-desc">' + escapeHtml(desc) + '</div>';
        html += '</div>';
      });
      html += '</div>';
    }

    // Other entities
    var others = (data.entities || []).filter(function (e) {
      return e.type !== 'principle' && e.type !== 'habit';
    });
    if (others.length > 0) {
      html += '<div class="context-section">';
      html += '<div class="context-section-title">🔧 Frameworks y Herramientas</div>';
      others.forEach(function (e) {
        var name = e.name || e.properties?.name || '—';
        var type = e.type || '';
        var desc = e.properties?.description || '';
        html += '<div class="context-item"><div class="item-name">' + escapeHtml(name) + '</div>';
        if (type) html += '<div class="item-desc" style="font-size:10px;color:#94a3b8;text-transform:uppercase;">' + escapeHtml(type) + '</div>';
        if (desc) html += '<div class="item-desc">' + escapeHtml(desc.substring(0, 120)) + (desc.length > 120 ? '…' : '') + '</div>';
        html += '</div>';
      });
      html += '</div>';
    }

    if (!html) {
      html = '<div class="context-empty">No hay contexto disponible para esta categoría.</div>';
    }

    container.innerHTML = html;
  }

  function escapeHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ── Init on DOM ready ──────────────────────────────────────────
  function init() {
    createPanel();
    var category = detectCategory();
    if (category) {
      loadContext(category);
    } else {
      var bodyEl = document.getElementById('context-panel-body');
      if (bodyEl) {
        bodyEl.innerHTML = '<div class="context-empty">Categoría no detectada desde la URL.</div>';
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
