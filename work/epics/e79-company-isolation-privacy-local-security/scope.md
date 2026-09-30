---
epic_id: E79
title: Aislamiento por empresa, privacidad y seguridad local
status: planned
jira_key: "ESCALA-42"
closure_disposition: active
created: 2026-09-12
updated: 2026-09-12
depends_on: []
related: [E37, E41, E42, E52, E55, E74, E78, E80, E81]
source_findings: [H03, H07, H08]
---

# Scope E79

## Objetivo y autoridad

Cero lecturas o escrituras cruzadas entre empresas; acceso local delimitado; consentimiento y promesas de privacidad verificables antes de compartir información.

E79 adelanta y posee el aislamiento mínimo urgente de E74; E74 reutiliza ese contrato para colaboración y reconciliación futura. No se implementan dos selectores, dos registries ni migraciones rivales.

**Estado:** planificado, implementación no iniciada. Los requisitos y pruebas son trabajo pendiente. Esta épica se registra en el backlog local canónico; no se afirma que exista un ticket remoto. [Programa de reparación](../../../governance/pilot-readiness-2026-09-12.md).

## Dentro

- Identidad y raíz de datos por empresa, con contexto explícito en todos los caminos de lectura/escritura.
- Migración conservadora de la base global legada y separación de caches/estado de sesión.
- Frontera HTTP/static, origen/host y acceso local autenticado, con límites de recursos.
- Mapa de datos local/proveedor IA, consentimiento, export de soporte y documentación verdadera.

## Fuera

- Servicio multiusuario en internet, SSO, OAuth propio o colaboración realtime.
- Reasignar hechos antiguos por similitud de nombres o compartir SQLite.
- Prometer control sobre retención/borrado del proveedor IA que ESCALA no puede ejercer.

## Decisiones y restricciones de diseño

1. Base y raíz local separadas por empresa mediante un resolver canónico; cada operación transporta una identidad opaca validada. La ausencia de identidad nunca abre una base global por defecto.
2. Cuando hay más de una empresa, la selección es explícita y visible; reanudar una sesión requiere validar la misma identidad, autorización y ubicación.
3. Los documentos compartibles futuros de E74 no convierten la base local en autoridad sincronizada. El resolver y el identificador creados aquí son reutilizables por E74.
4. Para el piloto se admite sólo loopback; cualquier soporte LAN requiere otra decisión y sus controles. CORS no sustituye autenticación ni verificación de Host/origen.
5. Antes de que el agente/modelo lea datos, explicar la frontera que efectivamente se puede controlar. El consentimiento de persistencia es distinto de autorizar una transmisión; un prompt no puede garantizar por sí solo aislamiento del proveedor.

Estos límites guían el diseño de historia; cualquier cambio que afecte contrato de empresa, migración o promesa pública debe quedar motivado y con prueba negativa. No se crea una segunda autoridad de estado o una capacidad pública paralela.

## Historias, requisitos y dependencias

El orden numérico identifica historias, no impone un orden topológico. Las dependencias de la tabla son obligatorias; las dependencias a épicas significan su entrega verificada. Las referencias relacionadas son coordinación, no un bloqueo artificial para reparar defectos existentes.

| Historia | Entrega | Tamaño | Dependencias duras | Estado | Requisito |
|---|---|:---:|---|---|---|
| S79.1 | Definir empresa activa y resolver único | M | Sin bloqueo técnico previo | planned | REQ-E79-001 |
| S79.2 | Aislar memoria, hojas, grafo y sesiones | L | S79.1 | planned | REQ-E79-002 |
| S79.3 | Migrar la instalación legada sin atribuciones inventadas | L | S79.1, S79.2, S78.5 | planned | REQ-E79-003 |
| S79.4 | Cerrar la frontera del servidor local | L | Sin bloqueo técnico previo | planned | REQ-E79-004 |
| S79.5 | Hacer explícito y verificable el flujo de datos | M | S79.1 | planned | REQ-E79-005 |
| S79.6 | Probar privacidad en integración y soporte | M | S79.2, S79.3, S79.4, S79.5, S78.6 | planned | REQ-E79-006 |

### S79.1 — Definir empresa activa y resolver único

**Componentes/archivos a inspeccionar:** escala_server/workspace/authority.py; CLI/servidor; sesión y contexto de coaching; contrato relacionado E74.

Como dueño de dos empresas quiero ver con cuál estoy trabajando antes de leer o guardar información.

**Criterios de aceptación — REQ-E79-001:**

- [ ] Crear contrato de identidad, raíz local y selección; rechazar raíz/ID desconocidos, traversal o identidad ausente con múltiples empresas.
- [ ] Separar explícitamente código instalado, datos por empresa y documentos de intercambio.
- [ ] Definir compatibilidad de una instalación de una sola empresa sin inferir automáticamente pertenencia de datos ambiguos.
- [ ] Registrar decisión arquitectónica consumible por S74.1/S74.2 y la frontera con el runtime E78.

**Validación:** Positiva: seleccionar A, cambiar a B y reanudar A. Negativas: mismo nombre con IDs distintos, ID inválido, symlink fuera de raíz y selección ambigua.

**Evidencia exigida:** Todas las entradas obtienen el mismo contexto validado y muestran la empresa activa sin exponer rutas privadas.

**Razón de secuencia:** Establece el contrato antes de modificar consultas o migrar información.

### S79.2 — Aislar memoria, hojas, grafo y sesiones

**Componentes/archivos a inspeccionar:** escala_server/memory_engine.py; graph_engine.py; daos; handlers.py; server.py; sesiones; coaching/evidence; persistencia y caches.

Como empresario quiero que cada recomendación y cada cambio usen exclusivamente la empresa autorizada.

**Criterios de aceptación — REQ-E79-002:**

- [ ] Propagar el contexto hasta facts, worksheets, graph, sessions, outcomes, dashboards y rutas de archivos; inventariar todos los accesos antes de cerrar.
- [ ] Eliminar contexto ignorado, claves globales y estado de clase compartido entre instancias que mezclen empresas.
- [ ] Aplicar aislamiento también a las capacidades conversacionales y a las rutas antiguas de YAML/Markdown, no sólo a la API.
- [ ] Incluir export, historial, cambio de empresa y concurrencia entre dos sesiones.

**Validación:** Positiva: dos empresas con categoría/herramienta y nombres idénticos conservan valores distintos. Negativas: ID de B con sesión de A, contexto omitido, cache caliente y dos instancias.

**Evidencia exigida:** Pruebas verifican cero lectura/escritura cruzada por API y conversación; cada consumidor del inventario tiene evidencia.

**Razón de secuencia:** Corrige el cruce reproducido H03 antes de permitir coexistencia real.

### S79.3 — Migrar la instalación legada sin atribuciones inventadas

**Componentes/archivos a inspeccionar:** migraciones de escala_server; rutas ~/.escala y .escala/.scaleup; registry por empresa.

Como usuario existente quiero conservar mi trabajo sin asignarlo al negocio equivocado.

**Criterios de aceptación — REQ-E79-003:**

- [ ] Generar inventario y preview local; datos sin dueño verificable permanecen pendientes hasta asignación explícita.
- [ ] Tomar snapshot consistente y ejecutar migración idempotente; conservar originales hasta verificación y aceptación.
- [ ] No usar coincidencia de nombre o categoría como prueba de empresa; no borrar datos ambiguos ni fusionar hechos en silencio.
- [ ] Restauración revierte la migración sin dejar permisos, caches o índices apuntando a otra empresa.

**Validación:** Positiva: legado de una empresa confirmado y legado mixto resuelto explícitamente. Negativas: cancelación, interrupción, dos nombres iguales y relaciones sin dueño.

**Evidencia exigida:** Conteos/hashes e identidades se concilian antes/después y una repetición no duplica registros.

**Razón de secuencia:** Consume el mecanismo de respaldo E78; evita arreglar aislamiento a costa de perder historia.

### S79.4 — Cerrar la frontera del servidor local

**Componentes/archivos a inspeccionar:** escala_server/server.py; cors.py; __main__.py; clientes HTTP/static.

Como usuario quiero que sólo las peticiones autorizadas accedan a mis datos locales.

**Criterios de aceptación — REQ-E79-004:**

- [ ] Comprobar pertenencia real de archivos con rutas normalizadas y límites de directorio; rechazar traversal, prefijos hermanos y symlinks fuera de static.
- [ ] Restringir origen y Host a los valores esperados; proteger APIs con credencial local de sesión que no aparezca en URLs, logs ni export.
- [ ] Mantener loopback obligatorio en el piloto; rechazar bind externo con explicación. Definir tratamiento seguro de peticiones sin Origin y de preflight.
- [ ] Limitar tamaño/tiempo de lectura de peticiones y manejar JSON/Content-Length inválidos sin exponer traceback o bloquear indefinidamente el proceso.

**Validación:** Positiva: navegador y cliente local autorizados. Negativas: archivo hermano, symlink, origen ajeno, Host ajeno, token ausente, cuerpo excesivo y lectura lenta.

**Evidencia exigida:** Pruebas de HTTP real confirman rechazo y ausencia de contenido sensible; no basta invocar sólo el manejador.

**Razón de secuencia:** Puede avanzar desde el inicio porque no depende de la migración de empresas.

### S79.5 — Hacer explícito y verificable el flujo de datos

**Componentes/archivos a inspeccionar:** README.md; PILOTO-EMPRESARIOS.md; escala-agent/README.md; skills de entrada/intake; adaptadores.

Como empresario quiero decidir qué información se guarda y qué puede recibir mi proveedor de IA.

**Criterios de aceptación — REQ-E79-005:**

- [ ] Documentar por modo: almacenamiento ESCALA, historial del agente, envío al modelo, herramientas externas y feedback; conservar fuentes oficiales y fecha de verificación.
- [ ] Mostrar explicación breve antes de habilitar lectura de archivos sensibles y registrar consentimiento por empresa/alcance; rechazar persistencia no autorizada.
- [ ] Distinguir control técnico real de instrucciones al modelo; si el agente no permite impedir una transferencia, declarar la limitación y ofrecer datos sintéticos/resumen manual.
- [ ] Describir retiro de consentimiento y eliminación local sin prometer borrar historiales o datos del proveedor fuera del control de ESCALA.

**Validación:** Positiva: autorización acotada y uso de datos sintéticos. Negativas: rechazo, cambio de empresa/proveedor/alcance y solicitud de borrado fuera del control local.

**Evidencia exigida:** El empresario puede explicar dónde queda y a quién se envía su información; docs y comportamiento coinciden.

**Razón de secuencia:** Corrige la promesa H07 antes de usar documentos reales en el piloto.

### S79.6 — Probar privacidad en integración y soporte

**Componentes/archivos a inspeccionar:** export público; exclusiones Git; feedback/outbox; reportes diagnósticos E78; tests de integración.

Como participante quiero reportar un fallo sin adjuntar la memoria de mi empresa.

**Criterios de aceptación — REQ-E79-006:**

- [ ] Excluir datos, backups, tokens, rutas privadas y conversaciones del artefacto público y del diagnóstico compartible por defecto.
- [ ] Generar localmente un preview mínimo de soporte; sólo exportarlo/compartirlo bajo autorización, sin telemetría nueva automática.
- [ ] Ensayar aislamiento, consentimiento, migración y HTTP juntos sobre un artefacto reparado E78.
- [ ] Entregar a E42 escenarios y a E81 formato mínimo de recibo con versión/error/etapa y referencia opaca.

**Validación:** Positiva: soporte recibe versión y error suficientes. Negativas: marcadores ficticios de secreto en nombres, logs, memoria y rutas nunca salen por el canal no autorizado.

**Evidencia exigida:** Escaneo y prueba negativa muestran cero filtraciones del fixture y todos los rechazos conservan datos aprobados.

**Razón de secuencia:** Une fronteras que por separado podrían pasar sus pruebas y fallar en el producto.

## Hitos y seguimiento

| Hito | Historias | Condición verificable | Fecha/real |
|---|---|---|---|
| M1 | S79.1, S79.4 | Identidad canónica y frontera HTTP segura. | Por planificar / pendiente |
| M2 | S79.2, S79.3, S79.5 | Dos empresas aisladas, legado conciliado y flujo de datos explicado. | Por planificar / pendiente |
| M3 | S79.6 | Recorrido integrado sin cruces ni filtración en soporte. | Por planificar / pendiente |

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

- La migración atribuye información mixta a una empresa: mantener cola local ambigua y exigir asignación verificable.
- Proteger API pero dejar bypass en skills/archivos: inventariar todos los consumidores y probar ambas rutas.
- Confundir consentimiento de guardado con privacidad del modelo: mapear y explicar el envío antes de habilitar lectura.

## Cómo iniciar y cerrar

Al iniciar una historia: leer este scope y [acceptance.md](acceptance.md), reproducir la línea base pertinente, diseñar el cambio acotado, implementar, verificar, revisar y documentar resultado. La creación de estos archivos no ejecuta ese ciclo ni autoriza contactar participantes o distribuir el producto.

La planificación sigue la estructura de `rai-epic-plan`. No existía un diseño específico previo para esta reparación: se parte de evidencia reproducida y los contratos existentes referenciados. Si el grafo o la sesión RaiSE no están disponibles, los artefactos locales siguen siendo revisables; no se simulan resultados de esas herramientas.
