---
epic_id: E86
title: Cash completo — lo que enseñó el curso de cash (versión 2026-10-14)
status: propuesto — versión 2, después de la revisión adversarial
created: 2026-10-15
updated: 2026-10-15
decision_owner: Eduardo Luna
fuente: sources/curso-cash/v2-2026-10-14/conocimiento/ (fuera del repo, sin nombres)
---

# Plan: Cash completo dentro de ESCALA (S86.13 – S86.31)

## Qué decidió Eduardo (2026-10-15)

1. **Sigue la épica E86** («ESCALA para el dueño», ESCALA-68). Cash crece dentro de ESCALA.
   El alcance de E86 decía «lógica de cálculo de Cash: fuera». Esta decisión lo cambia.
2. **Cada dueño fija sus límites.** ESCALA le pregunta. Los límites del curso son solo el punto de
   partida, y ESCALA dice que son de ejemplo («60 días, aquí inventado», audio del curso).
3. **Los 4 capítulos llevan una 5ª fila**, «salidas de capital». Sin ella no suman.
4. **Plan completo antes de programar.** Cada historia dice qué desarrollamos, qué logra el dueño
   y qué le muestra ESCALA.
5. **La prueba de que quedó bien es el escenario «analiza mi balance general y mi estado de resultados»**
   (ver abajo). Antes de programar: catálogo de fórmulas lámina por lámina, revisión propia y revisión adversarial.

## El escenario que define el éxito

El dueño dice «analiza mi balance general y mi estado de resultados» y manda sus estados como los tenga.

1. ESCALA lee lo que llegó y arma la lista de cuentas, sin calcular.
2. Muestra la lista de lo que necesita: ✔ lo tengo · ? no me queda claro · ✘ me falta.
3. Pregunta solo por los ? y ✘, máximo 3 preguntas por mensaje.
4. Revisa que todo cuadre (R1–R11). Si algo no cuadra, lo dice con el número y no calcula.
5. Dice qué va a calcular y qué no puede calcular, y por qué.
6. Calcula con la calculadora de Python. El modelo nunca hace cuentas.
7. Muestra «Tu contabilidad real» y los paneles, cada número con su fórmula y su lámina.

Lista completa de datos, preguntas y revisiones: `sources/curso-cash/v2-2026-10-14/conocimiento/entrada-escenario.md`
(se versiona como ficha en S86.15). Catálogo de las 86 láminas: `conocimiento/catalogo-laminas.md`.

**Este escenario funciona de punta a punta al cerrar la ola 1 (S86.17).** Las olas siguientes agregan paneles.

## Reglas que aplican a todas las historias

- **ESCALA nunca inventa ni supone un número.** Si falta un dato, pregunta. El modelo no hace cuentas.
- **Cada número lleva su fórmula y su origen** («sale de: clientes 5,639,601.55 ÷ (ventas 43,826,513.09 ÷ 365)»).
- **Una fórmula que no se puede calcular lo dice.** Base cero o negativa, dato faltante o periodo que no
  coincide → «no calculable: razón». Nunca un 0 en su lugar.
- **Ejemplo oficial: «Mi Empresa, S.A. de C.V.»** Es el dato de prueba de todas las historias.
- **Validación contra el curso.** Cada fórmula tiene una prueba con el número de la lámina.
  Donde la lámina tiene errata, la prueba usa el valor **correcto** y cita la errata. Ninguna prueba congela una errata.
- **Pruebas que pueden fallar.** Cada criterio se prueba con un caso que lo rompería
  (por ejemplo, cambiar una cuenta de caja debe cambiar el resultado).
- **Precisión fija.** Días con 2 decimales; porcentajes con 2. El color del semáforo se decide con el valor
  sin redondear. Los límites dicen si incluyen el borde.
- **Sin nombre del instructor ni de asistentes** en ningún archivo versionado. Se cita «Según el curso de cash que vimos».
- **Temas fiscales van al contador.** ESCALA muestra el renglón de ISR pero no recomienda.
- **Una sola puerta: `escala`.** El dueño no escribe comandos nuevos. ESCALA llama al cálculo por dentro.
- **Nada se guarda sin un «sí» del dueño**, y se guarda por empresa.
- TDD, un commit por tarea, una historia por rama, ciclo completo de RaiSE.

## Cómo llega todo al dueño

```
Dueño: «ESCALA, analiza mi balance general y mi estado de resultados»
   │
   ▼
Fase 1  Leer ───────────► Excel, CSV, PDF, foto o texto → lista de cuentas con monto (S86.14)
Fase 2  Lista ──────────► ✔ / ? / ✘ de lo que necesita (S86.17)
Fase 3  Preguntar ──────► máx. 3 por mensaje: caja de cada cuenta, IVA, crédito, retiros (S86.15)
Fase 4  Revisar ────────► R1–R11; si algo no cuadra, para y pregunta (S86.15)
Fase 5  Anunciar ───────► «con esto voy a calcular… no puedo calcular… porque…» (S86.17)
Fase 6  Calcular ───────► calculadora de Python; número + fórmula + origen (S86.16)
Fase 7  Mostrar ────────► paneles en work/cash/<empresa>/ (olas 2 y 3)
Fase 8  Decidir ────────► límites, simulador y, después, post-its con el board
```

## Lo que encontró la revisión del código que ya existe

| # | Hallazgo | Ejemplo con Mi Empresa | Historia |
|---|---|---|---|
| 1 | El poder del uno calcula bien la utilidad y **mal el flujo** en precio, volumen y costo. | Precio +1%: dice 438,265.13 de flujo; el curso dice 381,869.12. | S86.13 |
| 2 | La prueba de la línea 83 de `tests/test_cash_engine.py` confirma la fórmula equivocada. | Espera 240,000 donde el curso da menos. | S86.13 |
| 3 | El lector de Excel de E38 existe pero **ningún skill lo usa**, y no aguanta exportaciones reales (ver adversarial A4). | Buscar «ventas» encuentra «Costo de ventas». | S86.14 |
| 4 | Los procedimientos de cash piden al modelo que haga las cuentas. | Puede dar un número que no sale de los estados. | S86.16 |
| 5 | Faltan cuentas: préstamos, capital, otras cuentas, intereses, ISR, ventas a crédito, devoluciones, retiros. | Sin préstamos no hay deuda neta ni flujo neto. | S86.14, S86.15 |
| 6 | El «cambio en efectivo» usa caja final − caja inicial. El curso enseña que esa medida engaña. | +89,753.25 contra −3,705,245.84. | S86.20 |
| 7 | Hay límites inventados: CCC > 90, DSO > 60, margen < 30%, rangos por industria. | Ninguno sale del curso ni del dueño. | S86.16 |
| 8 | Skills y conocimiento duplicados (`escala-skills/` y `escala-agent/`). | Dos fuentes para la misma fórmula. | S86.27 |
| 9 | Solo existen periodos mensuales y multiplica ×12. | Un acumulado de 6 meses sale 6 veces más grande. | S86.15 |

## Lo que cambió con la revisión adversarial (15-oct-2026)

Detalle completo: página del catálogo, sección «Revisión adversarial». Lo comprobé con código antes de aceptarlo.

| # | Así iba a fallar | Cambio en el plan |
|---|---|---|
| A1 | Una cuenta en la caja equivocada no se detecta: los dos lados cambian igual y la 5ª fila lo absorbe. | «Otras cuentas» se calcula por renglones y se compara contra el residuo (S86.18). La 5ª fila se compara con los retiros que dijo el dueño; la diferencia se muestra como «sin explicar» (S86.20). |
| A2 | Documentos por pagar LP de Mi Empresa: la tasa de interés sobre la deuda bancaria da 32.91%; sumando los documentos, 9.98%. Pagan interés: son deuda. | Regla: si un pasivo paga interés, va a deuda neta. ESCALA pregunta (S86.15). Decisión 2 abajo. |
| A3 | El saldo de clientes trae IVA y las ventas no. Días de cobro 46.97 con IVA, 40.49 sin IVA: cambia el color. | Pregunta «¿tus clientes y proveedores incluyen IVA?» (S86.15). El panel dice qué base usó (S86.19). |
| A4 | El lector de Excel busca por pedazo de palabra, toma una sola fila por concepto, solo entiende fechas «2025-12», bloquea si no dice «pesos», bloquea todo dato con más de 90 días y descarta negativos entre paréntesis. | S86.14 nueva, solo para leer estados reales, con archivos de prueba de CONTPAQi y Aspel. |
| A5 | Un estado acumulado de 6 meses se multiplica ×12. | La pregunta «¿del mes o acumulado?» y la revisión de periodos pasan a la ola 1 (S86.15). |
| A6 | El simulador en vista mensual diría que subir el precio quita efectivo: mezcla el efecto de una vez (clientes) con el de cada mes (ventas). | S86.22 separa «efecto de una vez» y «efecto por periodo», y rotula «antes de ISR». |
| A7 | La calculadora no viaja en el paquete de Codex ni en el Agent Plugin. Sin ella, Cash no da nada. | S86.16 resuelve cómo se distribuye y prueba dentro del paquete construido. |
| A8 | El recorrido completo llegaba hasta la ola 4. Otros procedimientos seguían calculando con el modelo hasta la limpieza. | Esqueleto del escenario en la ola 1 (S86.17). Quitar cálculos del modelo y rangos por industria pasa a S86.16. |
| A9 | Ventas 0 da 0 días de cobro, que parece excelente; datos faltantes se rellenan con 0. | Regla «no calculable: razón» y pruebas con valores extremos (S86.16). |
| A10 | Proveedores 19.59 días: con redondeo sale «regular»; sin redondeo es «malo». | Regla de precisión fija (S86.21). |
| A11 | La fórmula propia del descuento (21.01%) olvida que el volumen extra también va con descuento. Correcta: 26.60%. | Corregida en S86.23. Decisión 1 abajo. |
| A12 | La carpeta con nombre del instructor ya no está versionada, y `door_bundle` ya copia todas las fichas. | Se quitan de la limpieza. |

## Historias

Tamaño en Fibonacci (1–8). Olas 1–4: 15 historias, 61 puntos. Ola 5 (después de probar con dueños reales): 4 historias, 14 puntos.

### Ola 1 — Base de verdad y el escenario de punta a punta

#### S86.13 — El poder del uno da el efectivo correcto · 3 puntos

- **Desarrollamos:**
  - Corregir el flujo de precio, volumen y costo en `escala_server/cash/__init__.py`.
  - Actualizar todo lo que usa el motor: la ruta `/api/cash/power-of-one`, el tablero (`dashboard.py`),
    `cash_decision.py` y sus pruebas (`test_e38_financial_intelligence.py`), no solo la línea 83.
  - Datos de prueba «Mi Empresa» (`tests/fixtures/cash/mi_empresa.yaml`), los dos años.
  - Pruebas de oro desde `verifica.py`, con los valores correctos donde hay errata.
  - Commit del cambio de `.gitignore` y de este plan.
- **El dueño logra:** saber cuánto efectivo le deja de verdad subir el precio 1%, sin cifras infladas.
- **ESCALA muestra:** el tablero actual del poder del uno, con el flujo correcto, rotulado «antes de ISR».
- **Validación:** flujo 381,869.12 / 146,818.75 / 235,050.36 / 134,210.40 / 120,072.64 / 62,921.82 / 62,921.82;
  total 1,143,864.91. Utilidad total 1,010,740.66. (El flujo neto ajustado se prueba en S86.20, porque necesita dos balances.)
- **Criterio verificable:** las 7 palancas al centavo; la suite completa pasa.
- ADVERTENCIA: los dueños que ya vieron el tablero vieron un flujo inflado. Decisión pendiente: avisarles o no.

#### S86.14 — ESCALA lee los estados como vienen · 5 puntos

- **Desarrollamos:** arreglar el lector de E38 para exportaciones reales.
  - Nombres en español con coincidencia por palabra completa y lista de exclusiones
    («Costo de ventas» no es «ventas»; «Anticipo de clientes» no es «clientes»).
  - Varias filas del mismo concepto se suman, con confirmación del dueño
    (gastos de venta + gastos de administración = gastos de operación).
  - Fechas «Dic-2025», «31/12/2025», «al 31 de diciembre de 2025».
  - Negativos entre paréntesis.
  - Si no encuentra la unidad, pregunta («¿pesos o miles de pesos?») en lugar de bloquear.
  - Un estado anual con más de 90 días no se bloquea: ESCALA dice la fecha y pregunta si hay algo más reciente.
  - PDF, foto o texto: el agente transcribe y repite las cifras para que el dueño las confirme.
    Aviso de posible dígito invertido cuando un total difiere de la suma por un múltiplo de 9.
- **El dueño logra:** mandar el archivo que le dio su contador, sin arreglarlo.
- **ESCALA muestra:** «así leí tus cuentas»: nombre original, monto y fecha.
- **Validación:** Mi Empresa en Excel, CSV y texto da la misma lista.
- **Criterio verificable:** archivos de prueba con forma de CONTPAQi y de Aspel (sintéticos) se leen completos;
  una prueba por cada falla de la lista de arriba.
- PRECAUCIÓN: el lector lo usa la decisión de cash de E38. Sus pruebas deben seguir pasando.

#### S86.15 — ESCALA pone cada cuenta en su caja y revisa que cuadre · 5 puntos

- **Desarrollamos:**
  - Mapa de cuentas a las 4 cajas del curso: capital de trabajo, deuda neta, otras cuentas, capital.
    Reglas escritas, con ejemplo:
    - pasivo que paga interés → deuda neta;
    - sobregiro bancario → deuda neta;
    - anticipo de clientes → otras cuentas.
  - Revisiones R1–R11 de `entrada-escenario.md`: cuadre del balance, utilidad = resultado del ejercicio
    (o resultados acumulados si ya se traspasó), subtotales, periodos, moneda, signos, caja de cada cuenta.
  - Preguntas de la primera vuelta:
    - C1 ventas a crédito;
    - C2 ¿todas las ventas o solo lo facturado?;
    - C3 retiros del dueño;
    - C4 dividendos;
    - ¿tus clientes y proveedores incluyen IVA?;
    - ¿el estado es del mes o acumulado?
  - Emparejar balance inicial y final del mismo periodo.
  - Ficha versionada: «Lo que ESCALA necesita para analizar tus estados».
- **El dueño logra:** que ESCALA entienda su contabilidad sin que él sepa contabilidad.
- **ESCALA muestra:** una tabla «así acomodé tus cuentas», con la caja de cada una y por qué.
  Debajo: «tu balance cuadra», o «no cuadra por 0.31: ¿redondeo o falta una cuenta?».
- **Validación:** Mi Empresa cuadra; la errata de 0.31 produce el aviso.
- **Criterio verificable:**
  - Mover una cuenta de caja cambia el resultado y dispara una pregunta.
  - Un acumulado de 6 meses nunca se multiplica por 12.

#### S86.16 — Una sola calculadora, que viaja con ESCALA · 5 puntos

- **Desarrollamos:**
  - `escala_server/cash/curso.py`: recibe estados ya revisados. Devuelve cada número con su fórmula,
    su origen y su lámina, en JSON. Si no puede calcular, devuelve «no calculable: razón».
  - Entrada interna (`python -m escala_server.cash.curso`) que la puerta llama.
  - Decidir y construir cómo llega la calculadora al dueño en Claude Code, Codex y Agent Plugin.
    Si no hay Python, ESCALA lo dice; no calcula de memoria.
  - Quitar el cálculo del modelo y los límites inventados de **todos** los procedimientos de cash:
    finanzas, 7 palancas, ciclo de efectivo, `escala-agent/skills/escala-cash` y los rangos por industria.
- **El dueño logra:** confiar en cada número; si pregunta «¿de dónde sale?», ve la cuenta.
- **ESCALA muestra:** debajo de cada cifra, «sale de: …».
- **Criterio verificable:**
  - La prueba corre **dentro del paquete construido**, no solo en el repo.
  - Una prueba recorre los procedimientos y falla si piden calcular «con tus capacidades» o traen rangos por industria.
  - Pruebas con valores extremos: ventas 0, UB negativa, sin inventario, sin costo (servicios).

#### S86.17 — El escenario «analiza mis estados», de punta a punta · 5 puntos

- **Desarrollamos:** el recorrido de las fases 1 a 6 dentro de la puerta `escala`.
  - Lista ✔ / ? / ✘ de lo que necesita.
  - Máximo 3 preguntas por mensaje, de la más importante a la menos importante.
  - «Con esto voy a calcular… No puedo calcular… porque…» (tabla de `entrada-escenario.md`).
  - Guardar los estados revisados en `work/cash/<empresa>/` solo con un «sí», con fecha de versión.
  - Si el dueño vuelve otro día, sigue donde quedó.
- **El dueño logra:** decir «analiza mi balance y mi estado de resultados» y recibir el análisis sin saber qué pedir.
- **ESCALA muestra:** la lista, las preguntas y, al final, un resumen con los números principales
  (capital de trabajo, días, ciclo, tres medidas) y su origen.
- **Criterio verificable:** prueba de punta a punta con 3 entradas:
  - Mi Empresa completa → calcula todo;
  - Mi Empresa sin el balance anterior → calcula lo estático y dice qué falta;
  - un estado sucio de prueba → pregunta antes de calcular.
  
  Ningún número lo escribe el modelo.

### Ola 2 — Paneles de lo que vimos en clase

#### S86.18 — Panel «Tu contabilidad real» · 3 puntos

- **Desarrollamos:** el balance simplificado (F2.1) y «por cada 100 de ventas» (F2.4).
  «Otras cuentas» se calcula sumando sus renglones y se compara contra el residuo.
- **El dueño logra:** ver cuánto dinero tiene atrapado en clientes, inventario y proveedores, y quién lo financia.
- **ESCALA muestra:** dos columnas, financiamiento contra operación.
  Ejemplo: «Por cada 100 pesos que vendes, 14.10 se quedan atrapados en capital de trabajo».
- **Validación:** financiamiento = operación = 15,014,008.75; CT por cada 100 = 14.10.
- **Criterio verificable:** si los renglones de otras cuentas no igualan al residuo, el panel no sale y ESCALA pregunta.

#### S86.19 — Panel «Días y ciclo del dinero» · 3 puntos

- **Desarrollamos:** días de clientes, inventario y proveedores (F2.2), cronograma (F2.3), dos años.
  Base con o sin IVA según la respuesta del dueño; días del periodo real (no siempre 365).
- **El dueño logra:** saber cuántos días tarda su dinero en regresar, y si empeoró.
- **ESCALA muestra:** línea de tiempo compra → pago → venta → cobro.
  Ejemplo: «Tu ciclo pasó de 37.07 a 55.53 días» y «días de cobro calculados con IVA».
- **Validación:** 36.08 → 46.97; 25.30 → 28.15; 24.31 → 19.59; sin IVA, clientes 40.49.
- **Criterio verificable:** sin ventas a crédito, usa ventas totales con aviso; sin costo, inventario y proveedores dicen «no aplica».

#### S86.20 — Panel «Las tres medidas de tu flujo» y los 4 capítulos · 5 puntos

- **Desarrollamos:** flujo neto (−Δ deuda neta), de operación (UO − ΔCT), marginal (%UB − %CT),
  y los 4 capítulos con la 5ª fila. El flujo neto ajustado del poder del uno.
- **El dueño logra:** entender por qué ganó dinero y aun así tiene menos efectivo.
- **ESCALA muestra:** cascada de 5 barras.
  Ejemplo: rentabilidad 5,018,095.92 − capital de trabajo 2,603,803.13 − **otras cuentas** 3,153,010.36
  − salidas de capital 2,966,528.27 = −3,705,245.84. «Otras cuentas» abre su desglose
  (activo fijo +320,732.86; pagos a acreedores 2,038,713.23; documentos LP 462,382.46…).
  La 5ª fila se compara con los retiros y dividendos que dijo el dueño. Si no coinciden: «sin explicar: X».
- **Validación:** −3,705,245.84; 4,835,206.16; 0.3350; flujo ajustado −2,561,380.93.
- **Criterio verificable:** la cascada suma al centavo **y** la 5ª fila se contrasta con la respuesta C3/C4.

#### S86.21 — Tu perfil ideal, con tus límites · 5 puntos

- **Desarrollamos:** porcentajes de $1 (F3b.1); preguntas para fijar ideal, regular y malo de 6 indicadores;
  guardar los límites por empresa, con un «sí»; ofrecer la versión B del curso como ejemplo.
  La contradicción de gastos en la versión B (óptimo < 33, regular 30–33) se le muestra al dueño para que la resuelva.
- **El dueño logra:** un semáforo con sus propias metas.
- **ESCALA muestra:** 6 tarjetas verde / amarillo / rojo con el valor exacto, la meta y la distancia.
  Ejemplo con la versión B: UB 47.60% regular; UO 16.97% malo; clientes 46.97 malo; proveedores 19.59 malo.
- **Criterio verificable:** sin límites guardados, ESCALA pregunta antes de pintar; el color usa el valor sin redondear.

#### S86.22 — Simulador de las 7 palancas · 5 puntos

- **Desarrollamos:** página con 7 controles. Python entrega dos coeficientes por palanca:
  efecto **de una vez** (lo que se queda en clientes, inventario o proveedores) y efecto **por periodo**
  (más venta, menos costo). La página multiplica cada uno por su lado.
- **El dueño logra:** probar «¿y si cobro 5 días antes y subo 2% el precio?».
- **ESCALA muestra:** barras de utilidad y flujo, rotuladas «antes de ISR», y advertencias del curso
  (precio: «alguno quedó fuera del mercado»; volumen: «crecer pide 14.10 por cada 100»).
  En empresas de servicios sin inventario, las palancas que no aplican se ven en gris con la razón.
- **Validación:** con las 7 en 1, el anual da 1,143,864.91 / 1,010,740.66.
- **Criterio verificable:** en vista mensual, subir el precio nunca resta efectivo por repetir el efecto de una vez.

### Ola 3 — Paneles de decisión

#### S86.23 — Precio contra volumen y el costo de un descuento · 3 puntos

- **Desarrollamos:** comparación precio/volumen (F3b.2), descuento (F3b.3) y el volumen de equilibrio.
- **El dueño logra:** saber, antes de dar un descuento, cuánto más tiene que vender para no perder.
- **ESCALA muestra:** «Si das 10% de descuento, necesitas vender 26.60% más solo para quedar igual».
  Para 10% y 15%: ver decisión 1.
- **Validación:** razones 2.10 y 2.60; volumen de equilibrio 26.60%.
- **Criterio verificable:** lo que no es del curso lleva la etiqueta «cálculo de ESCALA».

#### S86.24 — Margen antes de impuestos, salario de mercado y devoluciones · 3 puntos

- **Desarrollamos:** pre-tax (F6.1), sobre UB cuando el %UB es menor a 40% (F6.2), devoluciones (F6.3),
  pregunta del salario de mercado.
- **ESCALA muestra:** medidor del pre-tax con la línea del 10%; salario de mercado que dio el dueño.
- **Validación:** 15.47%; 6.35% y 16.50%; 17.45% y 30.16%.
- **Criterio verificable:** con UB o UAI negativas, F6.2 dice «no calculable» en lugar de un porcentaje positivo.

#### S86.25 — Las travesuras: ajustes que confiesa el dueño · 2 puntos

- **Desarrollamos:** preguntas por gastos personales pagados por la empresa; utilidad «como si no estuvieran».
- **Validación:** ajuste 97,942 → utilidad ajustada 5,463,710.03 (la lámina dice 5,463,260.03 por la errata).
- **Criterio verificable:** ESCALA solo suma los montos que dio el dueño. Lo fiscal va al contador.

### Ola 4 — Cierre

#### S86.26 — El recorrido con paneles y decisión · 3 puntos

- **Desarrollamos:** unir los paneles de las olas 2 y 3 al recorrido de S86.17; «vamos en la fase 7 de 8».
- **Criterio verificable:** prueba de recorrido con Mi Empresa, de los estados a todos los paneles.

#### S86.27 — Limpieza de duplicados · 2 puntos

- **Desarrollamos:** unir `escala-agent/skills/escala-cash` → `escala-skills/`; unir el conocimiento duplicado;
  actualizar `overview.md` de las fichas.
- **Criterio verificable:** una sola definición por fórmula.

### Ola 5 — Después de probar con 3 dueños reales (ver decisión 3)

| Historia | Qué | Por qué espera |
|---|---|---|
| S86.28 Evaluación instantánea · 5 | Reparto actual contra meta (L80–85) | Tabla de EE. UU., depende del tipo de cambio, los % suman 126.96% por traslape |
| S86.29 Los 5 caminos para crecer · 3 | Rendimiento 49.55% y gráfica (solo audio) | No está en las láminas |
| S86.30 Semana y trimestre · 3 | Vistas por periodo con balance de cada periodo | Una PyME casi nunca tiene balances semanales; la regla de mes o acumulado ya está en S86.15 |
| S86.31 Post-its con tu board · 3 | Ideas por palanca con su efecto en pesos | Necesita el simulador probado |

## Tickets para Jira (bajo ESCALA-68)

| Historia | Título | Tam. | Depende de |
|---|---|:---:|---|
| S86.13 | El poder del uno da el efectivo correcto | 3 | — |
| S86.14 | ESCALA lee los estados como vienen | 5 | — |
| S86.15 | ESCALA pone cada cuenta en su caja y revisa que cuadre | 5 | S86.14 |
| S86.16 | Una sola calculadora, que viaja con ESCALA | 5 | S86.13, S86.15 |
| S86.17 | El escenario «analiza mis estados», de punta a punta | 5 | S86.16 |
| S86.18 | Panel «Tu contabilidad real» | 3 | S86.17 |
| S86.19 | Panel «Días y ciclo del dinero» | 3 | S86.17 |
| S86.20 | Panel «Las tres medidas» y los 4 capítulos | 5 | S86.18 |
| S86.21 | Tu perfil ideal, con tus límites | 5 | S86.19 |
| S86.22 | Simulador de las 7 palancas | 5 | S86.16 |
| S86.23 | Precio contra volumen y descuento | 3 | S86.22 |
| S86.24 | Margen pre-tax, salario de mercado y devoluciones | 3 | S86.16 |
| S86.25 | Las travesuras | 2 | S86.16 |
| S86.26 | El recorrido con paneles y decisión | 3 | S86.18–S86.25 |
| S86.27 | Limpieza de duplicados | 2 | S86.16 |
| S86.28–31 | Ola 5 | 14 | Decisión 3 |

## Decisiones pendientes de Eduardo

1. **Descuento de 10% para vender 15% más.** La lámina suma los dos efectos por separado y da −1,253,643.95 de utilidad.
   El cálculo combinado (el volumen extra también va con descuento) da −1,911,041.64.
   Recomiendo: ESCALA muestra el combinado y dice «el curso lo simplifica sumando, y da −1,253,643.95».
2. **Documentos por pagar a largo plazo.** El curso los pone en «otras cuentas». Si pagan interés, son deuda,
   y el flujo neto de Mi Empresa cambia de −3,705,245.84 a −3,242,863.38.
   Recomiendo: ESCALA le pregunta al dueño; para Mi Empresa se queda como el curso, para que las pruebas cuadren con las láminas.
3. **Ola 5.** Recomiendo esperar a que 3 dueños reales pasen por las olas 1–4 antes de programarla.

Siguen abiertas, de antes: crear los tickets en Jira después de aprobar; avisar o no a los dueños del flujo inflado.

## Fuera de alcance

- Cálculo de impuestos y cualquier recomendación fiscal (incluida la PTU: ESCALA la muestra si viene, no la calcula).
- Escribir en la hoja del cliente.
- Pronósticos de flujo a futuro (el curso no los enseña).
- Personas físicas sin balance (por ejemplo, régimen simplificado): ESCALA dice que necesita un balance y no calcula los flujos.
