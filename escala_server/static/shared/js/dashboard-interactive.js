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
    onLoad: null,
    onModified: null,
    onSaved: null,
    hasData: false,
    modified: false,
    savedVersion: null
  };

  function init(config) {
    state.apiPath = config.apiPath;
    state.variables = JSON.parse(JSON.stringify(config.variables));
    state.variableKeys = config.variableKeys;
    state.variableMeta = config.variableMeta;
    state.onRecalc = config.onRecalc || function () {};
    state.onLoad = config.onLoad || function () {};
    state.onModified = config.onModified || function () {};
    state.onSaved = config.onSaved || function () {};
    state.containerId = config.containerId || 'sliders-container';

    loadFromServer();
  }

  function loadFromServer() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', state.apiPath, true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          var resp = JSON.parse(xhr.responseText);
          if (resp.data && resp.data.variables) {
            state.hasData = true;
            applySavedData(resp.data.variables);
          }
          state.onLoad(resp.meta || null, state.hasData, resp.data || {});
        } catch (e) { /* ignore parse errors */ }
      }
      renderSliders();
      runRecalc();
      setSavedIndicator(state.hasData ? 'saved' : 'empty');
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

      // Editable baseline
      var currentInput = document.createElement('input');
      currentInput.type = 'number';
      currentInput.className = 'baseline-input';
      currentInput.min = meta.min || 0;
      currentInput.max = meta.max || 100;
      currentInput.step = meta.step || 1;
      currentInput.value = v.current;
      currentInput.setAttribute('data-key', key);
      currentInput.setAttribute('aria-label', 'Línea base de ' + meta.label);
      currentInput.addEventListener('input', onCurrentChange);
      row.appendChild(currentInput);

      // Adjusted scenario range
      var slider = document.createElement('input');
      slider.type = 'range';
      slider.className = 'slider-input';
      slider.min = meta.min || 0;
      slider.max = meta.max || 100;
      slider.step = meta.step || 1;
      slider.value = v.adjusted;
      slider.setAttribute('data-key', key);
      slider.setAttribute('aria-label', 'Escenario de ' + meta.label);

      slider.addEventListener('input', onSliderChange);
      row.appendChild(slider);

      // Baseline label
      var currentDisplay = document.createElement('span');
      currentDisplay.className = 'slider-current';
      currentDisplay.textContent = 'Línea base';
      row.appendChild(currentDisplay);

      container.appendChild(row);
    }
  }

  function onCurrentChange(e) {
    var key = e.target.getAttribute('data-key');
    var val = parseFloat(e.target.value);
    if (!Number.isFinite(val)) return;
    state.variables[key].current = val;
    state.hasData = true;
    setModified(true);
    state.onModified();
    runRecalc();
  }

  function onSliderChange(e) {
    var key = e.target.getAttribute('data-key');
    var val = parseFloat(e.target.value);
    state.variables[key].adjusted = val;
    state.hasData = true;

    // Update value display
    var valueDisplay = document.getElementById('sv-' + key);
    if (valueDisplay) {
      valueDisplay.textContent = formatAdjusted(val, state.variableMeta[key]);
    }

    setModified(true);
    state.onModified();
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
        var response = {};
        try { response = JSON.parse(xhr.responseText); } catch (e) { /* metadata is optional */ }
        state.savedVersion = JSON.parse(JSON.stringify(state.variables));
        setModified(false);
        setSavedIndicator('saved');
        state.onSaved(response.meta || null);
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
    if (status === 'empty') {
      indicator.textContent = 'Pendiente de capturar';
      indicator.className = 'save-indicator modified';
    } else if (status === 'modified') {
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
