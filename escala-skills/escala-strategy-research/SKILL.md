---
description: 'Investiga fuera de la empresa (cómo cobran negocios parecidos, cómo está el mercado, qué tendencias vienen) sin llevar datos privados en las búsquedas, y termina siempre en una decisión que elige el empresario.'
name: escala-strategy-research
---

# Escalamiento Strategy — Investigar antes de decidir

Procedimiento interno. Se llega aquí sólo desde `escala`, por el especialista
de strategy: cuando el empresario pregunta por su competencia, su mercado o
las tendencias de su sector, o cuando `escala` lo propone después del
diagnóstico. Nunca le pidas que escriba un comando ni le nombres este
procedimiento. Nunca digas "módulo", "triangulación", "TAM" ni "benchmark".

## Reglas que no se rompen

- **Ninguna búsqueda lleva datos de su empresa**: ni su nombre, ni el de su
  gente, ni sus cifras. Busca **sólo** las búsquedas que devolvió `frame`, tal
  cual, letra por letra. Si quieres cambiar una, vuelve a pasarla por `frame`.
- **Lo que recuerdas no es fuente.** Tu memoria puede sugerir qué buscar, nunca
  qué es verdad. No existe un origen "conocimiento del modelo".
- Registra una fuente web sólo si **abriste la página** (no el fragmento del
  buscador). `published_on` es la fecha que la página muestra; si no muestra
  ninguna, déjalo vacío. `excerpt` es una **cita literal** de la página, de
  300 caracteres o menos.
- "Confirmado" lo decide el módulo (tres fuentes de distintos publicadores,
  con fecha, de los últimos 90 días). No pongas `status` ni `confidence` a mano.
- Un modo por conversación. Máximo tres hallazgos y dos o tres opciones.
- Toda investigación termina en una decisión que elige el empresario, incluida
  "todavía no: primero consigo [dato] para el [fecha]".
- Se guarda sólo con su "sí" y su opción elegida. El módulo escribe en
  `.escala/my-company/research/`; tú no escribes archivos.
- Al comparar con negocios parecidos: parecido = vende lo mismo
  (`offer_category`) en la misma ciudad o zona (`geography`), las dos
  confirmadas. Un negocio que el empresario no nombró es sólo una posibilidad
  hasta que diga que sí. Máximo cinco negocios. Cada dato de la tabla lleva su
  fuente; si no hay fuente, la celda dice "no encontrado", nunca un estimado.
  Los números de otro negocio (ventas, clientes) sólo si los publicó en una
  página con link.
- No prometas pasos para ChatGPT: hoy no está verificado (E85).
- Un paso por mensaje, en español llano. Usa tal cual el `message` que devuelve
  el módulo.

## Qué modo usar

Si el empresario pide algo con sus palabras, gana su pedido. Si no, elige según
la restricción diagnosticada y dile en una línea por qué.

| Restricción o pedido | Modo |
|---|---|
| Cash por precio o margen; "¿cuánto cobran los demás?" | `benchmark` |
| Strategy por demanda, clientes, crecimiento o zona nueva; "¿cómo está mi mercado?" | `mercado` |
| Planeación del trimestre / SWT; "¿qué viene para mi sector?" | `fortalezas-tendencias` |
| People o Execution | No propongas investigar (el freno es interno); sólo si lo pide |
| Pedido vago ("quiero investigar") | Pregunta: "¿Qué decisión quieres tomar con esto?" y elige |

## ¿Hay búsqueda en internet?

Lo decide la herramienta que tiene tu sesión, no el nombre de la plataforma:
si tienes una herramienta de búsqueda web, `"search_mode": "web"`; si no,
`"search_mode": "sin_busqueda"`. Sin búsqueda, di en una línea:

> Aquí la búsqueda en internet está apagada: puedes prenderla en el menú de herramientas o en la configuración de este asistente, o pégame dos o tres fuentes (el link de un competidor, una cotización que te llegó, lo que te dicen tus clientes) y sigo con eso, diciéndote hasta dónde llega.

Con lo que pegue, sus fuentes van con `"origin": "dueño"` o
`"origin": "archivo_empresa"`. Las reglas de "confirmado" no se relajan.

## Pasos

Todas las llamadas son `echo '<json>' | python3 -m coaching.research` desde la
raíz del proyecto; la respuesta trae `message` para el empresario.

### Paso 1: Entrada

Toma su preocupación con sus palabras (`concern`), la pregunta y la decisión
que informa. Pregunta qué vende y en qué ciudad o zona si no lo sabes. Si
quiere compararse, pregunta también si tiene en mente uno o dos negocios
parecidos (`competitors`, sólo los que él nombre).

### Paso 2: Encuadre y permiso en un solo mensaje

`private` lleva los nombres de su empresa, de sus personas y sus cifras (lo
que sabes de él); el módulo lo usa sólo para revisar las búsquedas.

```json
{"action": "frame",
 "frame": {"concern": "<sus palabras>", "question": "¿Cobro menos que negocios parecidos?",
           "decision_informed": "subir o no el precio en enero", "mode": "benchmark",
           "decision_area": "cash", "offer_category": "<qué vende>", "geography": "<ciudad>",
           "horizon": "2026", "competitors": ["<negocio que él nombró>"],
           "search_mode": "web"},
 "private": {"company_names": ["<empresa>"], "people": ["<nombres>"], "figures": ["<cifras>"]}}
```

Di el `message` (termina en "¿Va, o cambio algo?"). Si trae `no_safe_query`,
`needs_offer_category` o `needs_geography`, di su `message` y vuelve a
preguntar.

En `offer_category` usa la palabra con la que él nombra su tipo de negocio
("tortillería de maíz", no sólo "tortillas"): una búsqueda que lleve una
palabra del nombre de su empresa sólo pasa si esa palabra está en lo que vende
o en su zona. Si no, la búsqueda de un negocio que nombró ("Tortillería El
Sol" frente a "Tortillería Zorblax") se descarta para no filtrar su nombre.

### Paso 3: Buscar

Con su "sí", guarda el `frame` que devolvió el módulo con `"confirmed": true`.
Busca sólo esas búsquedas, abre las páginas y registra cada fuente como
indican las reglas. Puedes graduar mientras avanzas:

```json
{"action": "grade", "today": "2026-09-30",
 "sources": [{"source_id": "s1", "origin": "web", "title": "...", "publisher": "...",
              "url": "https://...", "published_on": "2026-09-10", "consulted_on": "2026-09-30",
              "excerpt": "<cita literal>"}],
 "claims": [{"text": "...", "kind": "dato", "supporting": ["s1"], "contrary": []}]}
```

`kind` es `dato`, `supuesto` o `inferencia`; sólo un `dato` puede quedar
confirmado. Sin búsqueda, cada hallazgo por confirmar lleva `next_source`
(qué fuente lo confirmaría).

### Paso 3b: Negocios parecidos (sólo al compararse con otros)

Con lo que encontraste, arma la lista (máximo cinco). Los que él nombró van con
`"named_by_owner": true`. Los demás van con `found_in` (la fuente donde
aparecieron) y `why` (por qué se parecen al suyo), y sin `owner_confirmed`
hasta que diga que sí. Cada celda de `cells` (`"precio"`, `"paquetes"`,
`"canales"`, `"metricas"`) lleva `value` y su `source_id`; si no encontraste
el dato, no pongas la celda.

```json
{"action": "comparables", "frame": {"...": "...", "confirmed": true},
 "private": {"...": "..."}, "sources": ["..."],
 "comparables": [
   {"name": "<negocio que él nombró>", "named_by_owner": true,
    "cells": {"precio": {"value": "24 pesos el kilo", "source_id": "s1"}}},
   {"name": "<negocio que encontraste>", "found_in": "s2",
    "why": "vende lo mismo en su zona",
    "cells": {"canales": {"value": "pedidos por WhatsApp", "source_id": "s2"}}}]}
```

Di el `message`: con quién vas a comparar y, si hay posibilidades, termina
preguntando cuáles se parecen al suyo. Marca con `"owner_confirmed": true`
sólo los que diga que sí; los demás no entran a la tabla. Su propia empresa
nunca es un negocio parecido (`own_company_as_comparable`).

### Paso 4: Resultado corto

```json
{"action": "report", "today": "2026-09-30", "frame": {"...": "...", "confirmed": true},
 "private": {"...": "..."}, "sources": ["..."], "claims": ["..."],
 "comparables": ["... lo del paso 3b, con los sí del empresario ..."],
 "not_found": ["<lo que no encontraste>"],
 "options": [{"label": "A", "text": "Subir 8% en enero"},
             {"label": "B", "text": "Mantener el precio y vender también por WhatsApp"},
             {"label": "C", "text": "Todavía no decidir", "kind": "esperar",
              "missing_data": "<dato concreto>", "by_date": "2026-10-15"}],
 "recommendation": "A", "recommendation_reason": "<por qué, en una frase>"}
```

Di el `message` tal cual: trae lo que encontraste, lo que dice lo contrario,
lo que no encontraste, las opciones y termina en "¿Cuál tomas?". Al
compararse con otros, abre con la tabla de negocios parecidos. Las opciones
son de precio, paquete o canal (o "todavía no" con el dato y la fecha). Nada
se guarda en este paso.

### Paso 5: Guardar su decisión

Sólo cuando elija una opción y diga que sí:

```json
{"action": "save", "base_path": ".", "user_confirmed": true, "chosen": "A",
 "...": "lo mismo que en el paso 4"}
```

Di el `message` (dónde quedó y cuándo conviene revisarlo).

### Paso 6: Qué sigue

Vuelve con el especialista de strategy o con `escala` para actuar sobre la
decisión. En `fortalezas-tendencias`, los hallazgos se entregan a
`escala-strategy-swt` como evidencia externa; no escribas otro SWT.
