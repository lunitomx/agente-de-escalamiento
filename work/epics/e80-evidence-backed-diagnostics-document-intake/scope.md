---
epic_id: E80
title: Diagnósticos honestos e ingreso de información útil
status: planned
jira_key: "ESCALA-43"
closure_disposition: active
created: 2026-09-12
updated: 2026-09-12
depends_on: []
related: [E37, E38, E40, E49, E52, E55, E73, E75, E78, E79, E81]
source_findings: [H04, H06, H09, H12]
---

# Scope E80

## Objetivo y autoridad

Un plan lleno de placeholders nunca aparece como negocio saludable; cada conclusión y gráfico explica evidencia, periodo, límites y siguiente acción.

E80 repara las superficies actuales de diagnóstico, dashboard e intake. E73 conserva la recomendación y generación avanzada de dashboards; E75 conserva deep dives. Se reutilizan facts y consentimiento de E49/E52/E55.

**Estado:** planificado, implementación no iniciada. Los requisitos y pruebas son trabajo pendiente. Esta épica se registra en el backlog local canónico; no se afirma que exista un ticket remoto. [Programa de reparación](../../../governance/pilot-readiness-2026-09-12.md).

## Dentro

- Semántica separada para completitud, cobertura/calidad de evidencia y desempeño.
- Corrección de scores, estados, prioridades y respuestas que ignoran contexto.
- PDF con texto seleccionable mediante extracción local acotada y fallback explícito para formatos no disponibles.
- Primera sesión y reanudación con una decisión, evidencia y compromiso confirmados.

## Fuera

- Certificar salud empresarial mediante un índice compuesto arbitrario.
- OCR universal, extracción cloud implícita o interpretación automática de cualquier estado financiero.
- Crear otro motor de facts, otro framework financiero o la biblioteca completa de procedimientos.

## Decisiones y restricciones de diseño

1. Un contrato de salida expresa tipo de indicador, definición, unidad, periodo, fuente, cobertura y estado; sólo se agregan métricas comparables.
2. Completitud usa schema y valores válidos; 'pendiente', whitespace o secciones inválidas no producen verde. Datos no observados conservan estado desconocido.
3. Dashboard y asesor consultan hechos autorizados del mismo contexto E79; la ruta sin modelo identifica orientación general cuando falta evidencia para personalizar.
4. PDF textual se procesa localmente con límites de tamaño/páginas y locators. Un PDF escaneado, cifrado o ambiguo produce una limitación y alternativa; no genera cifras inventadas.
5. La entrevista comparte el estado persistido E52/E55; el usuario confirma resumen, empresa y acción antes de reutilizar información sensible o contradictoria.

Estos límites guían el diseño de historia; cualquier cambio que afecte contrato de empresa, migración o promesa pública debe quedar motivado y con prueba negativa. No se crea una segunda autoridad de estado o una capacidad pública paralela.

## Historias, requisitos y dependencias

El orden numérico identifica historias, no impone un orden topológico. Las dependencias de la tabla son obligatorias; las dependencias a épicas significan su entrega verificada. Las referencias relacionadas son coordinación, no un bloqueo artificial para reparar defectos existentes.

| Historia | Entrega | Tamaño | Dependencias duras | Estado | Requisito |
|---|---|:---:|---|---|---|
| S80.1 | Definir qué mide cada indicador | M | Sin bloqueo técnico previo | planned | REQ-E80-001 |
| S80.2 | Corregir scores y prioridades del dashboard | M | S80.1 | planned | REQ-E80-002 |
| S80.3 | Usar contexto autorizado o declarar orientación general | M | S80.1, S79.2 | planned | REQ-E80-003 |
| S80.4 | Procesar PDF textual y ofrecer una salida recuperable | L | S79.5 | planned | REQ-E80-004 |
| S80.5 | Completar primera sesión y retomar sin fricción | M | S80.2, S80.3, S80.4, S79.2 | planned | REQ-E80-005 |
| S80.6 | Verificar coherencia entre conversación, API y dashboard | M | S80.2, S80.3, S80.4, S80.5, S78.6, S79.6 | planned | REQ-E80-006 |

### S80.1 — Definir qué mide cada indicador

**Componentes/archivos a inspeccionar:** escala_server/dashboard.py; executive/diagnostic.py; coaching/evidence; contrato de indicadores.

Como empresario quiero saber si un número describe mi documento, mis datos o mi desempeño.

**Criterios de aceptación — REQ-E80-001:**

- [ ] Inventariar scores y etiquetas actuales de los cuatro pilares y el resumen general.
- [ ] Definir completitud, evidencia y desempeño con unidad, periodo, cobertura, denominador y reglas de comparabilidad.
- [ ] Establecer estados sin datos, incompleto, inválido, vencido y comparable sin convertir ausencias en éxito.
- [ ] Eliminar la media global entre magnitudes incompatibles o etiquetarla sólo como avance documental si es consistente.

**Validación:** Positiva: datos comparables muestran indicador definido. Negativas: sólo un pilar, mezcla de periodos/unidades y ausencia total no producen salud global.

**Evidencia exigida:** Contrato y ejemplos aprobables explican cada indicador sin tecnicismos ni falsa precisión.

**Razón de secuencia:** Evita corregir sólo el valor 100 manteniendo una semántica equivocada.

### S80.2 — Corregir scores y prioridades del dashboard

**Componentes/archivos a inspeccionar:** escala_server/dashboard.py; static/index.html; coaching/strategy_opsp/engine.py; contratos de otros pilares.

Como empresario quiero que los pendientes y huecos sigan visibles aunque haya texto en todos los campos.

**Criterios de aceptación — REQ-E80-002:**

- [ ] Validar secciones con sus schemas; rechazar placeholders y contenido vacío/incorrecto.
- [ ] Aplicar etiquetas y estados del contrato en API y pantalla; no mostrar `good` por completitud como si fuera desempeño.
- [ ] Derivar prioridad de la preocupación y evidencia autorizada; diferenciar falta de datos de urgencia empresarial.
- [ ] Probar y documentar regresiones en Cash, People y Execution cuando se cambie el resumen compartido.

**Validación:** Positiva: plan válido muestra avance con etiqueta precisa. Negativas: ocho 'pendiente', whitespace, schema inválido y evidencia vencida nunca producen salud 100.

**Evidencia exigida:** API y dashboard muestran el mismo significado y la limitación se entiende sin leer documentación técnica.

**Razón de secuencia:** Corrige H04 en la superficie que realmente ve el usuario.

### S80.3 — Usar contexto autorizado o declarar orientación general

**Componentes/archivos a inspeccionar:** escala_server/business_advisor.py; memory/context; handlers de asesoría; skills de respuesta.

Como empresario quiero distinguir lo que ESCALA sabe de mi empresa de una guía general.

**Criterios de aceptación — REQ-E80-003:**

- [ ] Auditar rutas que reciben y no usan contexto; recuperar hechos de la empresa activa con fuente, periodo y autorización.
- [ ] Si faltan datos, formular una pregunta material y declarar el límite; no presentar plantillas generales como análisis de esa empresa.
- [ ] Cambiar o invalidar evidencia modifica las conclusiones dependientes; conservar reglas deterministas de cálculo existentes.
- [ ] Separar promesas del modo sin modelo de la conversación con el agente; ambos deben describir sus capacidades reales.

**Validación:** Positiva: dos contextos incompatibles generan conclusión o pregunta distinta donde corresponde. Negativas: contexto omitido, ajeno o stale no personaliza ni inventa cifras.

**Evidencia exigida:** Recibo enlaza afirmaciones empresariales a hechos autorizados o las etiqueta como hipótesis/orientación general.

**Razón de secuencia:** Consume aislamiento antes de aumentar uso de datos en recomendaciones.

### S80.4 — Procesar PDF textual y ofrecer una salida recuperable

**Componentes/archivos a inspeccionar:** escala_server/workspace/ingestion.py; profiling financiero; pyproject/manifiesto con E78; skills de intake.

Como empresario quiero aportar mi reporte sin tener que transcribirlo completo.

**Criterios de aceptación — REQ-E80-004:**

- [ ] Agregar extractor local acotado de PDF con texto, con dependencia declarada/reproducible y procedencia por página; verificar formato real, no sólo extensión.
- [ ] Mantener explícitos PDF escaneado/cifrado/corrupto, extractor ausente y tablas ambiguas; no seleccionar datos financieros sin confirmar periodo/unidad.
- [ ] Ofrecer CSV/XLSX/TXT o captura manual de los datos mínimos del caso, conservando continuidad y evitando re-preguntar hechos confirmados.
- [ ] Alinear capacidades reportadas, catálogo, instalación y mensajes; una alternativa manual no se contabiliza como extracción PDF exitosa.

**Validación:** Positiva: PDF textual sintético y archivo tabular equivalente producen hechos conciliables. Negativas: escaneado, contraseña, truncado, excesivo y moneda/periodo ambiguos.

**Evidencia exigida:** Fuente/página y confirmación acompañan al dato; ningún fallback convierte una limitación en éxito ficticio.

**Razón de secuencia:** Cierra H06 con soporte delimitado y alternativa útil, sin prometer lectura universal.

### S80.5 — Completar primera sesión y retomar sin fricción

**Componentes/archivos a inspeccionar:** coaching/welcome; sesión; escala-skills/escala; onboarding; persistencia E52/E55.

Como empresario quiero explicar mi problema y salir con un siguiente paso que pueda retomar.

**Criterios de aceptación — REQ-E80-005:**

- [ ] Entrar por una preocupación concreta, confirmar el resumen y pedir una sola aclaración material por turno.
- [ ] Aprovechar datos confirmados y señalar contradicciones/vigencia; no exigir nombres de skills ni calificaciones 1–5 para empezar.
- [ ] Producir decisión o hipótesis, fuente/límite, acción, responsable, fecha y revisión; mantener pendientes explícitos cuando falte evidencia.
- [ ] Cerrar/reabrir agente y proceso recupera sólo el estado consentido de la misma empresa; cambios del usuario invalidan conclusiones afectadas.

**Validación:** Positiva: primera acción y reanudación una semana después con estado persistido. Negativas: usuario rechaza guardar, cambia empresa, corrige cifra o no aporta datos suficientes.

**Evidencia exigida:** El recorrido conserva contexto útil y no inventa una decisión para cumplir el objetivo temporal del piloto.

**Razón de secuencia:** Integra intake, explicación y persistencia antes de medir utilidad humana.

### S80.6 — Verificar coherencia entre conversación, API y dashboard

**Componentes/archivos a inspeccionar:** tests de golden cases e integración; catálogo; README; guías piloto; adaptadores.

Como usuario quiero que las distintas pantallas y conversaciones describan la misma situación.

**Criterios de aceptación — REQ-E80-006:**

- [ ] Calificar un caso completo y adversariales por cada pilar incluido en el piloto.
- [ ] Verificar que API, conversación y dashboard no discrepan sobre empresa, periodo, dato, nivel de certeza ni acción.
- [ ] Entregar fixtures sintéticos a E68 para ejecución real de modelos; las aserciones de formato no sustituyen juicio semántico.
- [ ] Revisar el catálogo público, formatos y límites con ejemplos; conservar respuesta comprensible si una capacidad está ausente.

**Validación:** Positiva: mismo caso autorizado produce artefactos compatibles. Negativas: datos contradictorios, incompletos, placeholders y contexto cruzado son visibles y bloquean conclusiones dependientes.

**Evidencia exigida:** Recibo de integración por artefacto/versión, con límites del modo standalone y de cada adaptador.

**Razón de secuencia:** Evita que cada componente pase por separado mientras la experiencia empresarial contradice sus datos.

## Hitos y seguimiento

| Hito | Historias | Condición verificable | Fecha/real |
|---|---|---|---|
| M1 | S80.1, S80.2 | Indicadores interpretables y regresión de placeholders cerrada. | Por planificar / pendiente |
| M2 | S80.3, S80.4, S80.5 | Documento → evidencia → acción → reanudación con empresa autorizada. | Por planificar / pendiente |
| M3 | S80.6 | Coherencia de todas las superficies y handoff semántico a E68/E81. | Por planificar / pendiente |

Los cruces entre componentes se prueban antes del cierre final, mediante el último hito de integración. Se registran esfuerzo real y diferencias respecto del tamaño al cerrar cada historia; no se inventa velocidad ni duración.

## Criterios de terminación

- [ ] Los seis requisitos tienen evidencia exacta y trazable al commit/artefacto ejecutado.
- [ ] Casos positivos, negativos y de recuperación aplicables pasan en el límite real que se afirma proteger.
- [ ] Todos los hallazgos asignados tienen disposición explícita; no se considera reparación una etiqueta o un fixture verde.
- [ ] Documentación, interfaz, comandos y capacidades anunciadas coinciden con el comportamiento observado.
- [ ] Una revisión independiente comprueba correctness, regresiones y fronteras de datos al implementar; no se presume realizada en esta planificación.
- [ ] Retrospectiva y handoff a las épicas relacionadas actualizan el backlog sin alterar sus gates de aceptación.
- [ ] La evidencia humana/hardware exigida está presente o se conserva el gate pendiente; no se fabrica para cerrar.

## Riesgos y mitigaciones

- Cambiar colores sin corregir el significado: validar el contrato y comprensión humana de la etiqueta.
- Prometer PDF universal: delimitar textual/escaneado/cifrado y contabilizar fallback por separado.
- Subir la tasa de primera acción inventando certeza: nunca penalizar una limitación honesta ni premiar una respuesta sin evidencia.

## Cómo iniciar y cerrar

Al iniciar una historia: leer este scope y [acceptance.md](acceptance.md), reproducir la línea base pertinente, diseñar el cambio acotado, implementar, verificar, revisar y documentar resultado. La creación de estos archivos no ejecuta ese ciclo ni autoriza contactar participantes o distribuir el producto.

La planificación sigue la estructura de `rai-epic-plan`. No existía un diseño específico previo para esta reparación: se parte de evidencia reproducida y los contratos existentes referenciados. Si el grafo o la sesión RaiSE no están disponibles, los artefactos locales siguen siendo revisables; no se simulan resultados de esas herramientas.
