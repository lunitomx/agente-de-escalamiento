/**
 * Dashboard Interactive — reusable JS module for interactive dashboards.
 *
 * Provides:
 * - Slider creation with labels
 * - Save/load via Escala Server API
 * - Modified vs saved indicator
 *
 * Usage:
 *   DashboardInteractive.init({
 *     apiPath: '/api/worksheets/cash/power-of-one',
 *     variables: { ... },   // default values
 *     variableKeys: ['price', 'volume', ...],
 *     variableMeta: { price: { label: 'Precio', min: 0, max: 100, step: 1, unit: '$' }, ... },
 *     onRecalc: function(vars) { ... },  // called on each slider change
 *     containerId: 'sliders-container'
 *   });
 */

var DashboardInteractive = (function () {
  'use strict';

  var state = {
    apiPath: '',
    variables: {},
    variableKeys: [],
    variableMeta: {},
    onRecalc: null,
    modified: false,
    savedVersion: null
  };

  function init(config) {
    state.apiPath = config.apiPath;
    state.variables = JSON.parse(JSON.stringify(config.variables));
    state.variableKeys = config.variableKeys;
    state.variableMeta = config.variableMeta;
    state.onRecalc = config.onRecalc || function () {};
    state.containerId = config.containerId || 'sliders-container';

    loadFromServer();
  }

  function applySavedData(savedVars) {
    var keys = state.variableKeys;
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (savedVars[key] !== undefined) {
        state.variables[key].current = savedVars[key].current || 0;
        state.variables[key].adjusted = savedVars[key].adjusted || 0;
      }
    }
    state.savedVersion = JSON.parse(JSON.stringify(state.variables));
  }

  function loadFromServer() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', state.apiPath, true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          var resp = JSON.parse(xhr.responseText);
          // Handle both {data: {variables: ...}} and {data: {data: {variables: ...}}}
          var payload = resp.data || {};
          if (payload.data && payload.data.variables) {
            applySavedData(payload.data.variables);
          } else if (payload.variables) {
            applySavedData(payload.variables);
          }
        } catch (e) { /* ignore parse errors */ }
      }
      renderSliders();
      runRecalc();
      setSavedIndicator('saved');
    };
    xhr.send();
  }

  function applySavedData(savedVars) {
    var keys = state.variableKeys;
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (savedVars[key] !== undefined) {
        state.variables[key].current = savedVars[key].current || 0;
        state.variables[key].adjusted = savedVars[key].adjusted || 0;
      }
    }
    state.savedVersion = JSON.parse(JSON.stringify(state.variables));
  }

  function renderSliders() {
    var container = document.getElementById(state.containerId);
    if (!container) return;
    container.innerHTML = '';

    var keys = state.variableKeys;
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      var meta = state.variableMeta[key];
      var v = state.variables[key];

      var row = document.createElement('div');
      row.className = 'slider-row';

      // Label
      var label = document.createElement('label');
      label.className = 'slider-label';
      label.textContent = meta.label;
      row.appendChild(label);

      // Slider value display
      var valueDisplay = document.createElement('span');
      valueDisplay.className = 'slider-value';
      valueDisplay.id = 'sv-' + key;
      valueDisplay.textContent = formatAdjusted(v.adjusted, meta);
      row.appendChild(valueDisplay);

      // Range input
      var slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'slider-input';
      slider.min = meta.min || 0;
      slider.max = meta.max || 100;
      slider.step = meta.step || 1;
      slider.value = v.adjusted;
      slider.setAttribute('data-key', key);

      slider.addEventListener('input', onSliderChange);
      row.appendChild(slider);

      // Current value (baseline)
      var currentDisplay = document.createElement('span');
      currentDisplay.className = 'slider-current';
      currentDisplay.textContent = 'Base: ' + PowerOfOneEngine.formatValue(v.current, meta.unit);
      row.appendChild(currentDisplay);

      container.appendChild(row);
    }
  }

  function onSliderChange(e) {
    var key = e.target.getAttribute('data-key');
    var val = parseFloat(e.target.value);
    state.variables[key].adjusted = val;

    // Update value display
    var valueDisplay = document.getElementById('sv-' + key);
    if (valueDisplay) {
      valueDisplay.textContent = formatAdjusted(val, state.variableMeta[key]);
    }

    setModified(true);
    runRecalc();
  }

  function runRecalc() {
    if (state.onRecalc) {
      var impacts = PowerOfOneEngine.calcImpacts(state.variables);
      state.onRecalc(state.variables, impacts);
    }
  }

  function save() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', state.apiPath, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
      if (xhr.status === 200) {
        state.savedVersion = JSON.parse(JSON.stringify(state.variables));
        setModified(false);
        setSavedIndicator('saved');
      }
    };
    var payload = JSON.stringify({
      variables: state.variables,
      timestamp: new Date().toISOString()
    });
    xhr.send(payload);
  }

  function setModified(isModified) {
    state.modified = isModified;
    setSavedIndicator(isModified ? 'modified' : 'saved');
  }

  function setSavedIndicator(status) {
    var indicator = document.getElementById('save-indicator');
    if (!indicator) return;
    if (status === 'modified') {
      indicator.textContent = '✏️ Modificado';
      indicator.className = 'save-indicator modified';
    } else {
      indicator.textContent = '💾 Guardado';
      indicator.className = 'save-indicator saved';
    }
  }

  function formatAdjusted(val, meta) {
    if (meta.unit === '$') return '$' + Math.round(val).toLocaleString();
    if (meta.unit === '%') return val.toFixed(1) + '%';
    if (meta.unit === 'd') return Math.round(val) + 'd';
    return val.toLocaleString();
  }

  function getVariables() {
    return state.variables;
  }

  return {
    init: init,
    save: save,
    getVariables: getVariables
  };
})();
