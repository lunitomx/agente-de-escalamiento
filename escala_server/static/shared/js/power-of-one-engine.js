/**
 * Power of One — Calculation Engine
 *
 * Extracted from the original E14 Power of One dashboard.
 * Computes CF and EBIT monetary impact for all 7 variables.
 */

var PowerOfOneEngine = (function () {
  'use strict';

  /**
   * Computes CF and EBIT monetary impact for all 7 Power of One variables.
   * @param {Object} vars - { price: {current, adjusted}, volume: {...}, ... }
   * @returns {Array<{key, cfImpact, ebitImpact}>}
   */
  function calcImpacts(vars) {
    var revenue = vars.price.current * vars.volume.current;
    var dailyRevenue = revenue / 365;

    return [
      { key: 'price',     cfImpact: (vars.price.adjusted     - vars.price.current)     * vars.volume.current,         ebitImpact: (vars.price.adjusted     - vars.price.current)     * vars.volume.current },
      { key: 'volume',    cfImpact: (vars.volume.adjusted    - vars.volume.current)    * vars.price.current,          ebitImpact: (vars.volume.adjusted    - vars.volume.current)    * vars.price.current },
      { key: 'cogs',      cfImpact: -((vars.cogs.adjusted     - vars.cogs.current)     / 100) * revenue,              ebitImpact: -((vars.cogs.adjusted     - vars.cogs.current)     / 100) * revenue },
      { key: 'overheads', cfImpact: -(vars.overheads.adjusted - vars.overheads.current),                              ebitImpact: -(vars.overheads.adjusted - vars.overheads.current) },
      { key: 'ar_days',   cfImpact: -(vars.ar_days.adjusted   - vars.ar_days.current)   * dailyRevenue,               ebitImpact: 0 },
      { key: 'inv_days',  cfImpact: -(vars.inv_days.adjusted  - vars.inv_days.current)  * dailyRevenue,               ebitImpact: 0 },
      { key: 'ap_days',   cfImpact:  (vars.ap_days.adjusted   - vars.ap_days.current)   * dailyRevenue,               ebitImpact: 0 }
    ];
  }

  /**
   * Determine status class for a variable row.
   * Threshold: ±5% of base revenue.
   */
  function statusFor(cfImpact, ebitImpact, revenue) {
    if (revenue === 0 || (cfImpact === 0 && ebitImpact === 0)) return 'semaforo-gray';
    var threshold = Math.abs(revenue) * 0.05;
    if (cfImpact >= threshold && ebitImpact >= threshold) return 'semaforo-green';
    if (cfImpact <= -threshold && ebitImpact <= -threshold) return 'semaforo-red';
    return 'semaforo-yellow';
  }

  /**
   * Aggregate status for summary row.
   */
  function aggregateStatus(totalCF, totalEBIT) {
    if (totalCF === 0 && totalEBIT === 0) return 'semaforo-gray';
    if (totalCF > 0 && totalEBIT >= 0) return 'semaforo-green';
    if (totalCF < 0 && totalEBIT <= 0) return 'semaforo-red';
    return 'semaforo-yellow';
  }

  function statusLabel(cls) {
    var labels = {
      'semaforo-green':  'Mejora',
      'semaforo-yellow': 'Neutral',
      'semaforo-red':    'Retroceso',
      'semaforo-gray':   'Sin datos'
    };
    return labels[cls] || '—';
  }

  function formatCurrency(n, signed) {
    var abs = Math.abs(n);
    var formatted = abs.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
    if (signed) return n > 0 ? '+' + formatted : (n < 0 ? '-' + formatted : formatted);
    return formatted;
  }

  function formatValue(v, unit) {
    if (unit === '$') return v.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
    if (unit === '%') return v.toFixed(1) + '%';
    return v.toLocaleString('en-US') + unit;
  }

  return {
    calcImpacts: calcImpacts,
    statusFor: statusFor,
    aggregateStatus: aggregateStatus,
    statusLabel: statusLabel,
    formatCurrency: formatCurrency,
    formatValue: formatValue
  };
})();
