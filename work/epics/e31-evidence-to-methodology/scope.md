# Epic Scope: E31 — Evidencia Operativa a Metodologías

**Status:** Planned
**Dependencies:** E22 (memoria local), E25 (guía de conectores), E26 (workspace), E27 (diagnóstico narrativo), E29 (Business Pulse)
**Tamaño:** XL

## Outcome

Una persona no técnica pasa de “mi foco es Cash / People / Strategy / Execution”
a trabajar con la metodología adecuada y evidencia operativa real. El agente
pide únicamente el dato mínimo, propone el canal de captura y persiste sólo los
campos que la persona confirma, con fuente y fecha visibles.

## Disparadores de producto

1. Al terminar una decisión narrativa, antes de presentar un score como verdad:
   “¿Quieres cuantificar esto ahora con datos reales o mantenerlo como
   diagnóstico cualitativo?”
2. Cuando el foco confirmado sea una de las cuatro decisiones y la persona
   pida profundizar.
3. Cuando diga “tengo un Excel / reporte / archivo”, “quiero trabajar mi caja”,
   “conecta Drive/Calendar/CRM” o abra una metodología sin datos suficientes.

## In scope

- Conversación de decisión: continuar cualitativo, capturar manualmente,
  previsualizar un archivo o usar una capacidad de conector disponible en el
  host.
- Contrato de evidencia: fuente, fecha observada, tipo, campos propuestos,
  aprobación por campo, confianza y estado de vigencia.
- Previsualización local de CSV/XLSX y contenido que el conector del host
  entregue explícitamente; detectar secretos, PII y datos delicados antes de
  guardar o indexar.
- Mapeo verificable de datos hacia metodologías, comenzando por:
  - Cash: Power of One y Cash Conversion Cycle;
  - Execution: prioridades, KPI y ritmo de reuniones;
  - People: roles/capacidad y FACe sin perfilar personas;
  - Strategy: cliente, promesa y plan en una hoja.
- Solicitud progresiva de datos faltantes: sólo los necesarios para el método
  elegido, con alternativa manual si no hay archivo/conector.
- Paneles que muestran procedencia, fecha, dato pendiente y posibilidad de
  corregir/reemplazar una fuente.
- Pruebas de consentimiento, archivos malformados, columnas ambiguas,
  información sensible, datos viejos, hosts sin MCP y reconstrucción local.

## Out of scope

- Instalar MCPs, OAuth, credenciales, scraping, sincronización automática o
  acceso silencioso a Drive, Calendar, CRM o contabilidad.
- Interpretar que una carpeta, un archivo o una cuenta conectada autoriza
  almacenar todo su contenido.
- Convertir un archivo financiero en recomendación legal, fiscal o de inversión.
- Sustituir al contador, CRM o sistema contable como fuente de verdad.
- Entrenar modelos, telemetría remota o subir documentos empresariales a un
  servicio externo desde ScaleUp.

## Reglas no negociables

1. La narrativa va antes del número; el dato se pide cuando desbloquea una
   decisión o metodología concreta.
2. El usuario elige fuente, alcance y persistencia; el conector del host sólo
   entrega contenido cuando el usuario lo autorizó ahí.
3. Se muestra una previsualización y mapeo antes de persistir; se pueden aceptar,
   editar o rechazar campos individualmente.
4. Cada número guardado conserva fuente, fecha observada y método de captura.
5. Sin evidencia suficiente, el panel dice “Pendiente” y explica qué falta; no
   rellena ceros ni inventa ratios.
6. Los archivos originales y datos sensibles no se indexan ni comparten por
   defecto; se conserva sólo lo que la persona confirme como necesario.

## Historias

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S31.1 — Contrato de evidencia y consentimiento por campo | L | Fuente, fecha, mínimo dato, preview y corrección trazables. |
| 2 | S31.2 — Enrutamiento “narrativa → metodología” | L | El agente sabe cuándo ofrecer cuantificación y cuál herramienta corresponde. |
| 3 | S31.3 — Ingesta local de archivos con preview seguro | XL | CSV/XLSX se leen localmente, se detecta riesgo y se propone un mapeo. |
| 4 | S31.4 — Contexto procedente de MCPs del host | L | Contenido autorizado por el host sigue el mismo preview, con fallback manual. |
| 5 | S31.5 — Mapeadores Cash y paneles con procedencia | XL | Power of One/CCC se llenan con datos confirmados, no con placeholders. |
| 6 | S31.6 — Mapeadores People, Strategy y Execution | XL | Cada decisión pide sólo datos operativos útiles y los lleva a su metodología. |
| 7 | S31.7 — Evaluación, privacidad e instalación | L | E2E, adversariales, fuentes viejas y smokes Claude/Codex/Hermes. |

## Acceptance criteria

- [ ] Una respuesta narrativa detallada no se reduce obligatoriamente a 1–5; la
  persona puede mantenerla cualitativa o pedir cuantificación.
- [ ] Para Cash, el agente explica qué siete variables necesita antes de pedir
  un archivo o valores: precio, volumen, COGS, gastos, A/R, inventario y A/P.
- [ ] Un CSV/XLSX se previsualiza y propone columnas; ningún dato se persiste
  hasta que la persona confirme los campos.
- [ ] Un dato proporcionado mediante MCP conserva que vino del host, cuándo fue
  observado y qué campo de metodología alimenta; un host sin MCP sigue teniendo
  una ruta manual completa.
- [ ] Secretos, identificadores y contenido delicado detienen o minimizan la
  captura antes de memoria, índice, dashboard o workspace compartido.
- [ ] Power of One/CCC y al menos una metodología por las otras tres decisiones
  muestran datos reales confirmados o un estado pendiente accionable.
- [ ] La corrección o sustitución de fuente actualiza el panel sin destruir el
  historial ni ocultar su procedencia.
- [ ] El flujo se instala y funciona desde el único skill público en Claude,
  Codex y Hermes, sin pedir rutas, JSON ni jerga técnica.
