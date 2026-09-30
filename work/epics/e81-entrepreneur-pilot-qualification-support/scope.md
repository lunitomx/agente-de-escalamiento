---
epic_id: E81
title: Piloto empresarial de 3–5 a 20 participantes y soporte medible
status: planned
closure_disposition: active
created: 2026-09-12
updated: 2026-09-12
depends_on: [E78, E79, E80]
related: [E10, E42, E44, E45, E68, E70]
source_findings: [H09, H10, H11, H12]
---

# Scope E81

## Objetivo y autoridad

Una decisión de ampliar, iterar o detener sustentada en 3–5 sesiones acompañadas y una cohorte posterior de 20 instalaciones independientes.

E81 organiza adopción y soporte del piloto; E42 sigue siendo dueño de hardware/aceptación y E68 de semántica/paridad/ciclo trimestral. Se reutilizan sus recibos por commit/hash/plataforma y nunca se sustituyen por métricas de uso.

**Estado:** planificado, implementación no iniciada. Los requisitos y pruebas son trabajo pendiente. Esta épica se registra en el backlog local canónico; no se afirma que exista un ticket remoto. [Programa de reparación](../../../governance/pilot-readiness-2026-09-12.md).

## Dentro

- Matriz de modos/agentes/SO realmente ofrecidos y recorrido de dos sesiones.
- Protocolo de observación, soporte privado, registro mínimo consentido y definiciones de métricas.
- Cohorte acompañada de 3–5 y posterior cohorte de 20, con decisiones de paso explícitas.
- Evaluación de utilidad contra la línea base y reporte honesto de abandono/costo operativo.

## Fuera

- Contactar o inscribir empresarios automáticamente; usar datos reales sin autorización.
- Declarar completa E42/E68, rebajar sus criterios o reemplazar un trimestre por una semana.
- Telemetría automática, CRM/mesa de ayuda cloud o publicación automática del producto.

## Decisiones y restricciones de diseño

1. Recibos privados locales con referencia opaca de participante, etapa, versión, plataforma, tiempos, asistencia y resultado; nunca anexar transcripciones/archivos reales al repositorio.
2. La cohorte acompañada sirve para descubrir fricción; no se contabiliza como instalación autónoma. La cohorte de 20 se mide por separado.
3. Congelar criterios antes de invitar: los umbrales del protocolo son objetivos propuestos de producto, no resultados observados ni promesas.
4. Un fallo de red del laboratorio se registra como limitación del entorno; no prueba un defecto de producto ni una instalación offline exitosa.
5. Una decisión de no ampliar puede cerrar la evaluación E81 si existe evidencia completa y aceptación explícita, pero no declara reparado el producto ni autoriza release. Las reparaciones pendientes mantienen abiertas sus épicas propietarias.

Estos límites guían el diseño de historia; cualquier cambio que afecte contrato de empresa, migración o promesa pública debe quedar motivado y con prueba negativa. No se crea una segunda autoridad de estado o una capacidad pública paralela.

## Historias, requisitos y dependencias

El orden numérico identifica historias, no impone un orden topológico. Las dependencias de la tabla son obligatorias; las dependencias a épicas significan su entrega verificada. Las referencias relacionadas son coordinación, no un bloqueo artificial para reparar defectos existentes.

| Historia | Entrega | Tamaño | Dependencias duras | Estado | Requisito |
|---|---|:---:|---|---|---|
| S81.1 | Fijar matriz ofrecida y protocolo de aceptación | M | Sin bloqueo técnico previo | planned | REQ-E81-001 |
| S81.2 | Preparar soporte y reporte local mínimo | M | S81.1, S78.6, S79.6 | planned | REQ-E81-002 |
| S81.3 | Observar 3–5 empresarios acompañados | L | S81.1, S81.2, E78, E79, E80 | planned | REQ-E81-003 |
| S81.4 | Medir autonomía en una cohorte de 20 | L | S81.3 | planned | REQ-E81-004 |
| S81.5 | Evaluar utilidad y costo frente a la línea base | M | S81.1, S81.3 | planned | REQ-E81-005 |
| S81.6 | Decidir ampliación y transferir los pendientes | M | S81.4, S81.5 | planned | REQ-E81-006 |

### S81.1 — Fijar matriz ofrecida y protocolo de aceptación

**Componentes/archivos a inspeccionar:** PILOTO-EMPRESARIOS.md; protocolos E42/E68; matriz de producto y versiones.

Como responsable del piloto quiero saber exactamente qué estamos invitando a probar.

**Criterios de aceptación — REQ-E81-001:**

- [ ] Elegir un agente y plataforma inicial por evidencia; declarar experimental cualquier combinación no calificada.
- [ ] Reutilizar los ocho pasos de E42 y una segunda sesión de seguimiento; registrar commit/hash, OS, Python, agente/modelo y condiciones iniciales.
- [ ] Separar recepción del artefacto, prerrequisitos, instalación y primera acción para medir toda la fricción.
- [ ] Congelar participantes/denominadores, objetivos, reglas de privacidad y criterios de suspensión antes de iniciar.

**Validación:** Positiva: cada combinación anunciada enlaza a recibo vigente. Negativas: etiqueta 'windows' de fixture Linux, recibo de otro hash y capacidades no distribuidas no califican.

**Evidencia exigida:** Protocolo y matriz versionados; E42/E68 conservan su autoridad y no se exige cerrar un piloto para poder preparar su protocolo.

**Razón de secuencia:** Puede prepararse antes de cerrar E78–E80; su ejecución externa depende de las reparaciones.

### S81.2 — Preparar soporte y reporte local mínimo

**Componentes/archivos a inspeccionar:** escala-health; feedback/outbox; guía del participante; runbook de soporte.

Como empresario quiero recuperarme de un error y compartir sólo lo necesario si pido ayuda.

**Criterios de aceptación — REQ-E81-002:**

- [ ] Crear guía de recuperación para instalación, proveedor/agente, permisos, formato, actualización, estado perdido y empresa equivocada.
- [ ] Consumir diagnóstico E78 y preview/redacción E79; reporte local con versión, etapa, error y pasos voluntarios.
- [ ] Registrar minutos y tipo de asistencia por participante, incluso si abandona o nunca llega a la primera sesión.
- [ ] Definir responsable de soporte y canal elegido por el dueño antes del piloto; preparar plantillas sin enviar mensajes ni tickets automáticamente.

**Validación:** Positiva: soporte reproduce el fallo con fixture y metadata mínima. Negativas: negarse a compartir funciona y el reporte no incluye datos/credenciales/rutas privadas.

**Evidencia exigida:** Runbook probado con incidentes sembrados y registro que distingue autoservicio de ayuda humana.

**Razón de secuencia:** Evita reclutar 20 usuarios sin un mecanismo para observar y atender fallos.

### S81.3 — Observar 3–5 empresarios acompañados

**Componentes/archivos a inspeccionar:** protocolo de piloto privado; recibos E42; experiencia de primera/segunda sesión.

Como equipo de producto queremos ver dónde se interrumpe el recorrido con usuarios reales.

**Criterios de aceptación — REQ-E81-003:**

- [ ] Reclutar sólo con autorización; comenzar con datos sintéticos/no sensibles y después usar únicamente material consentido.
- [ ] Observar instalar → aportar evidencia → decidir → guardar → reabrir → revisar; registrar ayudas y bloqueos, no completar silenciosamente por el usuario.
- [ ] Exigir cero cruces/pérdidas/exposiciones de datos y recuperación correcta en todos los casos con persistencia autorizada.
- [ ] Para pasar a 20: al menos tres participantes evaluables, ≥80% completa una primera acción sustentada y ≥80% logra la segunda sesión; documentar n y redondear al entero superior.
- [ ] Asignar correcciones a E78/E79/E80 y repetir casos afectados; no ampliar con incidentes críticos abiertos.

**Validación:** Positiva: registros de sesiones reales y artefactos locales recuperados. Negativas: abandono, no consentimiento o caso inconcluso quedan registrados, no sustituidos por fixtures.

**Evidencia exigida:** Decisión explícita de pasar/iterar con n=3–5, asistencia y criterios congelados; disponibilidad humana sigue siendo dependencia externa.

**Razón de secuencia:** Descubre fricción antes de multiplicar el soporte.

### S81.4 — Medir autonomía en una cohorte de 20

**Componentes/archivos a inspeccionar:** protocolo de cohorte; recibos privados; registro consentido de soporte.

Como dueño del producto quiero comprobar si veinte empresarios pueden usarlo sin mi intervención continua.

**Criterios de aceptación — REQ-E81-004:**

- [ ] Invitar veinte participantes distintos de la cohorte acompañada, con combinación ofrecida respaldada por E42 y pruebas reales del agente según E68.
- [ ] Medir a todos desde que reciben las instrucciones; registrar quienes no empiezan, fallan prerrequisitos o abandonan.
- [ ] Objetivos propuestos: ≥18/20 instala sin ayuda humana; ≥15/20 obtiene acción sustentada en ≤20 minutos de primera sesión; ≥14/20 vuelve entre días 5 y 10.
- [ ] Exigir cero pérdida/cruce/exposición de datos y 100% recuperación correcta entre quienes guardaron y comprobaron reanudación; informar el denominador y los casos no observados.
- [ ] Medir soporte total por persona: mediana ≤15 minutos durante diez días como objetivo, más p90, total y causas; no ocultar intervención del fundador.

**Validación:** Positiva: cohorte completa con denominadores y evidencia de ambas sesiones. Negativas: no iniciados y asistidos no cuentan como éxitos autónomos; no observados no se convierten en recuperaciones exitosas.

**Evidencia exigida:** Dataset privado mínimo y reporte agregado con valores observados, objetivos y excepciones separados.

**Razón de secuencia:** Depende de la aceptación de paso y de cero incidentes críticos; no se ejecuta sólo porque exista este documento.

### S81.5 — Evaluar utilidad y costo frente a la línea base

**Componentes/archivos a inspeccionar:** línea base E42; resultados E44/E45; rúbrica de valor y registros del piloto.

Como responsable del producto quiero saber si ESCALA mejora decisiones además de producir texto.

**Criterios de aceptación — REQ-E81-005:**

- [ ] Comparar con la línea base de E42 y, donde proceda, coach único de E45; mantener pregunta/evidencia/modelo comparables y registrar diferencias.
- [ ] Revisar trazabilidad, claridad, acción con responsable/fecha y capacidad de corregir un error; no usar longitud o tono como proxy de calidad.
- [ ] Separar primera impresión, acción ejecutada y resultado observado; 'todavía sin resultado' es válido.
- [ ] Documentar tamaño de muestra, sesgo por asistencia y costo/tiempo observados; no atribuir cambios del negocio causalmente al agente.

**Validación:** Positiva: evaluación humana puede explicar por qué la acción fue útil. Negativas: respuesta convincente sin evidencia, conclusión errónea o ausencia de ventaja no se promueven.

**Evidencia exigida:** Comparación reproducible y limitada; si no hay muestra comparable, se declara pendiente y no se inventa superioridad.

**Razón de secuencia:** Puede evaluarse tras la cohorte pequeña y enriquecerse con la de veinte.

### S81.6 — Decidir ampliación y transferir los pendientes

**Componentes/archivos a inspeccionar:** informe final piloto; backlog canónico; handoff E42/E68/E70.

Como dueño quiero decidir ampliar, corregir o detener con evidencia completa.

**Criterios de aceptación — REQ-E81-006:**

- [ ] Publicar sólo un informe local agregado/redactado con funnel, tiempos, asistencia, incidentes, causas y limitaciones.
- [ ] Mapear cada hallazgo inicial y nuevo a reparación/evidencia vigente; conservar incidentes sin resolver y su propietario.
- [ ] Registrar decisión humana de ampliar/iterar/detener; una decisión adversa no borra datos ni cambia umbrales retrospectivamente.
- [ ] Entregar a E70 matriz y riesgos; E42 sigue requiriendo sus plataformas y E68 su paridad/ciclo trimestral. No ejecutar distribución como efecto del cierre.

**Validación:** Positiva: decisión enlaza criterios congelados y resultados reales. Negativas: sólo fixtures, menos de veinte sin explicación o datos omitidos impiden afirmar cohorte de veinte calificada.

**Evidencia exigida:** Evaluación completa, aceptación real y backlog actualizado; readiness del producto se mantiene bloqueada si los objetivos o reparaciones no se cumplieron.

**Razón de secuencia:** Cierra aprendizaje del piloto sin convertirlo en autorización automática de release.

## Hitos y seguimiento

| Hito | Historias | Condición verificable | Fecha/real |
|---|---|---|---|
| M1 | S81.1, S81.2 | Matriz, protocolo y soporte listos; reparaciones verificadas antes de reclutar. | Por planificar / pendiente |
| M2 | S81.3 | 3–5 empresarios observados y decisión explícita de ampliar/iterar. | Por planificar / pendiente |
| M3 | S81.4, S81.5 | Cohorte de veinte medida, utilidad y carga de soporte conocidas. | Por planificar / pendiente |
| M4 | S81.6 | Decisión humana e informe con pendientes y handoff a gates existentes. | Por planificar / pendiente |

Los cruces entre componentes se prueban antes del cierre final, mediante el último hito de integración. Se registran esfuerzo real y diferencias respecto del tamaño al cerrar cada historia; no se inventa velocidad ni duración.

## Criterios de terminación

- [ ] Los seis requisitos tienen evidencia exacta y trazable al commit/artefacto ejecutado.
- [ ] Casos positivos, negativos y de recuperación aplicables pasan en el límite real que se afirma proteger.
- [ ] Todos los hallazgos asignados tienen disposición explícita; no se considera reparación una etiqueta o un fixture verde.
- [ ] Documentación, interfaz, comandos y capacidades anunciadas coinciden con el comportamiento observado.
- [ ] Una revisión independiente comprueba correctness, regresiones y fronteras de datos al implementar; no se presume realizada en esta planificación.
- [ ] Retrospectiva y handoff a las épicas relacionadas actualizan el backlog sin alterar sus gates de aceptación.
- [ ] La evidencia humana/hardware exigida está presente o se conserva el gate pendiente; no se fabrica para cerrar.

En E81, una evaluación completada puede concluir `iterar` o `detener` con aceptación humana. Esa decisión no satisface por sí misma la preparación para distribución: los objetivos incumplidos e incidentes mantienen abierto el programa y las reparaciones correspondientes.

## Riesgos y mitigaciones

- Contar asistencia como autonomía: separar cohortes y registrar cada intervención.
- Presionar para mostrar éxito: congelar métricas y conservar no iniciados/abandono en denominadores.
- Esperar el cierre completo de E42/E68 para observar humanos genera un ciclo: usar sus evidencias parciales por combinación y conservar sus gates de cierre completos.

## Cómo iniciar y cerrar

Al iniciar una historia: leer este scope y [acceptance.md](acceptance.md), reproducir la línea base pertinente, diseñar el cambio acotado, implementar, verificar, revisar y documentar resultado. La creación de estos archivos no ejecuta ese ciclo ni autoriza contactar participantes o distribuir el producto.

La planificación sigue la estructura de `rai-epic-plan`. No existía un diseño específico previo para esta reparación: se parte de evidencia reproducida y los contratos existentes referenciados. Si el grafo o la sesión RaiSE no están disponibles, los artefactos locales siguen siendo revisables; no se simulan resultados de esas herramientas.
