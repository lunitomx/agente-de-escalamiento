/*
 * Simulador de las 7 palancas (S86.22). Esta página sólo multiplica.
 *
 * Los coeficientes por punto (1% o 1 día) llegan de Python, con su fórmula y su
 * origen. Aquí no hay ninguna fórmula de negocio:
 *   cada periodo = Σ movimiento × coeficiente "por_periodo" ÷ meses de la vista
 *   una sola vez = Σ movimiento × coeficiente "una_vez"   (nunca se reparte ni se repite)
 * El total (cada periodo + una sola vez) sólo existe cuando la vista cubre todo
 * el periodo de los estados (meses = 1). En la vista mensual va aparte: mezclar
 * un mes con algo que pasa una vez haría creer que subir el precio resta efectivo.
 */
(function (raiz) {
  'use strict';

  function centavos(x) {
    var signo = x < 0 ? -1 : 1;
    return (signo * Math.round(Math.abs(x) * 100 + 1e-7)) / 100;
  }

  function razonDe(parte) {
    if (parte && parte.no_aplica) return parte.no_aplica;
    if (parte && parte.no_calculable) return 'no calculable: ' + parte.no_calculable;
    return null;
  }

  function aplica(p) {
    return Boolean(p.por_periodo && p.por_periodo.valor !== undefined &&
      p.una_vez && p.una_vez.valor !== undefined);
  }

  function simular(datos, movimientos, claveVista) {
    var vista = null;
    for (var i = 0; i < datos.vistas.length; i++) {
      if (datos.vistas[i].clave === claveVista) vista = datos.vistas[i];
    }
    if (vista === null) throw new Error('vista desconocida: ' + claveVista);
    var periodo = 0;
    var unaVez = 0;
    var palancas = [];
    var avisos = [];
    datos.palancas.forEach(function (p) {
      var si = aplica(p);
      var mov = si ? Number((movimientos || {})[p.palanca] || 0) : 0;
      var cadaPeriodo = si ? (mov * Number(p.por_periodo.valor)) / vista.meses : 0;
      var deUnaVez = si ? mov * Number(p.una_vez.valor) : 0;
      periodo += cadaPeriodo;
      unaVez += deUnaVez;
      palancas.push({
        palanca: p.palanca,
        aplica: si,
        razon: si ? null : (razonDe(p.por_periodo) || razonDe(p.una_vez)),
        movimiento: mov,
        cada_periodo: centavos(cadaPeriodo),
        una_vez: centavos(deUnaVez)
      });
      if (mov > 0) {
        datos.advertencias.forEach(function (a) {
          if (a.palanca === p.palanca) avisos.push(a.palanca);
        });
      }
    });
    return {
      vista: vista.clave,
      meses: vista.meses,
      utilidad: centavos(periodo),
      efectivo_cada_periodo: centavos(periodo),
      una_vez: centavos(unaVez),
      efectivo_total: vista.meses === 1 ? centavos(periodo + unaVez) : null,
      advertencias: avisos,
      palancas: palancas
    };
  }

  // ---------------------------------------------------------------- página

  function formato(x) {
    return x.toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function cifra(el, x) {
    el.textContent = formato(x);
    el.className = 'cifra' + (x > 0 ? ' pos' : x < 0 ? ' neg' : '');
  }

  function crear(tag, clase, texto) {
    var el = document.createElement(tag);
    if (clase) el.className = clase;
    if (texto !== undefined) el.textContent = texto;
    return el;
  }

  function pintar() {
    var fuente = document.getElementById('datos-simulador');
    if (!fuente || !document.getElementById('palancas')) return;
    var datos = JSON.parse(fuente.textContent);
    var estado = { vista: datos.vistas[0].clave, movimientos: {} };
    var lados = {};

    function etiqueta(p, mov) {
      return (mov > 0 ? '+' : '') + mov + (p.unidad === '%' ? '%' : (Math.abs(mov) === 1 ? ' día' : ' días'));
    }

    function actualizar() {
      var r = simular(datos, estado.movimientos, estado.vista);
      var vista = datos.vistas.filter(function (v) { return v.clave === estado.vista; })[0];
      document.querySelectorAll('[data-vista-nombre]').forEach(function (el) {
        el.textContent = '(' + vista.nombre.toLowerCase() + ')';
      });
      cifra(document.getElementById('utilidad'), r.utilidad);
      cifra(document.getElementById('efectivo-cada-periodo'), r.efectivo_cada_periodo);
      cifra(document.getElementById('una-vez'), r.una_vez);
      var total = document.getElementById('efectivo-total');
      var nota = document.getElementById('nota-total');
      if (r.efectivo_total === null) {
        total.textContent = 'va aparte';
        total.className = 'cifra';
        nota.textContent = 'En esta vista lo de una sola vez no se suma a cada mes: pasa una vez.';
      } else {
        cifra(total, r.efectivo_total);
        nota.textContent = 'Cada periodo + una sola vez.';
      }
      r.palancas.forEach(function (p) {
        if (lados[p.palanca]) {
          lados[p.palanca].textContent = 'Cada periodo: ' + formato(p.cada_periodo) +
            ' · Una sola vez: ' + formato(p.una_vez);
        }
      });
      var avisos = document.getElementById('avisos');
      avisos.textContent = '';
      datos.advertencias.forEach(function (a) {
        if (r.advertencias.indexOf(a.palanca) === -1) return;
        var caja = crear('div', 'aviso');
        caja.appendChild(crear('b', null, 'Aviso: '));
        caja.appendChild(document.createTextNode(a.texto + ' (' + a.origen + '; ' + a.lamina + ')'));
        avisos.appendChild(caja);
      });
    }

    var botones = document.getElementById('vistas');
    datos.vistas.forEach(function (v) {
      var b = crear('button', null, v.nombre);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(v.clave === estado.vista));
      b.addEventListener('click', function () {
        estado.vista = v.clave;
        botones.querySelectorAll('button').forEach(function (o) {
          o.setAttribute('aria-pressed', String(o === b));
        });
        actualizar();
      });
      botones.appendChild(b);
    });

    var lista = document.getElementById('palancas');
    datos.palancas.forEach(function (p) {
      var si = aplica(p);
      var fila = crear('div', 'palanca' + (si ? '' : ' gris'));
      var nombre = crear('div');
      nombre.appendChild(crear('div', 'nombre', p.nombre));
      nombre.appendChild(crear('div', 'mejora', si ? 'Mejorar es ' + p.mejora : ''));
      fila.appendChild(nombre);
      if (si) {
        var limite = p.unidad === '%' ? datos.rango_pct : datos.rango_dias;
        var control = document.createElement('input');
        control.type = 'range';
        control.min = String(-limite);
        control.max = String(limite);
        control.step = '1';
        control.value = '0';
        control.setAttribute('aria-label', p.nombre);
        var mov = crear('div', 'mov', etiqueta(p, 0));
        control.addEventListener('input', function () {
          var n = parseInt(control.value, 10);
          estado.movimientos[p.palanca] = n;
          mov.textContent = etiqueta(p, n);
          actualizar();
        });
        fila.appendChild(control);
        fila.appendChild(mov);
        var detalle = crear('div', 'lados');
        detalle.title = p.por_periodo.formula + ' (' + p.por_periodo.origen + ') · ' +
          p.una_vez.formula + ' (' + p.una_vez.origen + ')';
        lados[p.palanca] = detalle;
        fila.appendChild(detalle);
      } else {
        var razon = crear('div', 'razon', 'No se mueve: ' + (razonDe(p.por_periodo) || razonDe(p.una_vez)));
        razon.style.gridColumn = '2 / -1';
        fila.appendChild(razon);
      }
      lista.appendChild(fila);
    });
    actualizar();
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { simular: simular };
  } else {
    raiz.SimuladorEscala = { simular: simular };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', pintar);
    } else {
      pintar();
    }
  }
})(this);
