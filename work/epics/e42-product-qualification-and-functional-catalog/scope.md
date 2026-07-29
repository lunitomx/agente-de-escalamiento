---
epic_id: "E42"
title: "Product Qualification and Functional Catalog"
status: "local_qualification_pass"
created: "2026-07-22"
updated: "2026-07-29"
release: "ESCALA Local V2"
---

# E42 — Producto probado y catálogo verdadero

## Objetivo

Demostrar de extremo a extremo qué puede hacer ESCALA en una máquina limpia y
entregar una descripción honesta, verificable y entendible del producto.

**Valor:** antes de incorporar aprendizaje agentic, el producto obtiene una
línea base real de instalación, utilidad, claridad, evidencia y límites.

## Historias

| ID | Historia | Tamaño | Estado | Requisitos |
|---|---|:---:|:---:|---|
| S42.1 | Viaje completo e instalaciones limpias | L | local_qualification_pass | REQ-E42-001, REQ-E42-003 |
| S42.2 | Inventario y prueba real de skills | M | local_qualification_pass | REQ-E42-002 |
| S42.3 | Escenarios de seguridad y recuperación | M | local_qualification_pass | REQ-E42-004 |
| S42.4 | Catálogo, PDF y aceptación humana | M | local_qualification_pass | REQ-E42-005, REQ-E42-006 |

## S42.1 — Viaje completo e instalaciones limpias

### Experiencia

Una empresa de prueba inicia sin preparación especial y recorre:

1. instalación;
2. creación del espacio local;
3. ingreso de documentos;
4. análisis de reuniones;
5. análisis Cash;
6. preguntas de Strategy;
7. cockpit ejecutivo;
8. acción y seguimiento.

### Termina cuando

- El recorrido se repite en macOS y Windows con versiones y artefactos exactos.
- Cada paso guarda evidencia sin incluir información sensible.
- Los bloqueos y preguntas se registran como parte del resultado.
- No se usa un servidor hospedado ni una base compartida.

## S42.2 — Inventario y prueba real de skills

### Experiencia

El equipo de producto puede responder, para cada skill:

- ¿Qué problema empresarial resuelve?
- ¿Qué información necesita?
- ¿Qué resultado entrega?
- ¿Cómo se ve un caso exitoso?
- ¿Cómo falla cuando falta información?
- ¿Fue invocado realmente o solo existe como archivo?

### Termina cuando

- Todo skill entregado aparece una sola vez en el inventario.
- Cada skill tiene propósito, prerrequisitos, caso positivo y caso negativo.
- Existe un recibo de invocación actual.
- Los skills duplicados, obsoletos o no demostrados se marcan como tales; no se
  esconden.

## S42.3 — Escenarios de seguridad y recuperación

### Experiencia

ESCALA falla de forma segura cuando:

- un archivo está dañado;
- la evidencia está vencida;
- se intenta alterar un paquete;
- una actualización se interrumpe;
- no existe conexión;
- se intenta sincronizar SQLite;
- una carpeta compartida pretende convertirse en autoridad.

### Termina cuando

- Cada escenario produce un resultado comprensible y recuperable.
- Ningún escenario pierde la información local existente.
- Los rechazos explican al empresario qué ocurrió y cuál es el siguiente paso.
- Privacidad y recuperación se validan en la matriz declarada.

## S42.4 — Catálogo, PDF y aceptación humana

### Experiencia

Un empresario recibe un catálogo y un PDF en español que explican:

- qué hace ESCALA;
- qué evidencia respalda cada funcionalidad;
- qué archivos necesita;
- qué limitaciones existen;
- qué sigue pendiente;
- qué información permanece local.

### Termina cuando

- El catálogo coincide con la evidencia y el inventario.
- El PDF no menciona fuentes privadas o materiales prohibidos.
- Las limitaciones se explican sin lenguaje técnico innecesario.
- El dueño del producto registra aceptación explícita requisito por requisito.
- La aceptación humana no se sustituye con pruebas automáticas.

## Criterios de terminación de la épica

- [x] REQ-E42-001: recorrido completo probado (local/sintético).
- [x] REQ-E42-002: inventario y casos de todos los skills (local/sintético).
- [ ] REQ-E42-003: aceptación en macOS y Windows limpios (pendiente de hardware).
- [x] REQ-E42-004: fallas negativas y recuperación segura (local/sintético).
- [x] REQ-E42-005: catálogo y PDF verificables.
- [ ] REQ-E42-006: auditoría final y aceptación humana (pendiente).
- [x] Las cuatro historias tienen retrospectiva.
- [x] La evidencia diferencia pruebas sintéticas, hardware real y aceptación humana.
- [x] No se publicó ni se transfirieron datos sin autorización.

## Línea base para E43-E46

E42 medirá, sin ampliar el producto:

| Métrica | Pregunta empresarial |
|---|---|
| Tiempo a la primera acción | ¿Cuánto tarda el empresario en obtener algo que puede hacer? |
| Evidencia visible | ¿Puede saber de dónde salió la recomendación? |
| Preguntas necesarias | ¿Cuánta aclaración se necesitó antes de ser útil? |
| Errores detectados | ¿ESCALA encontró contradicciones y cálculos sembrados? |
| Claridad | ¿El empresario entendió la respuesta sin explicación técnica? |
| Confianza | ¿Usaría esta recomendación para decidir? |
| Seguimiento | ¿La recomendación terminó en una acción con responsable? |

Estas medidas son la comparación obligatoria para E43-E46. Si una nueva capa
agentic no mejora la línea base, no se promueve.

## Dependencias

```text
S42.1 Viaje completo
   ├── S42.2 Inventario verdadero
   └── S42.3 Seguridad y recuperación
            └── S42.4 Catálogo y aceptación
```

- E37-E41 cerradas localmente con su evidencia.
- Acceso a una máquina macOS limpia.
- Acceso a una máquina Windows limpia.
- Participación de al menos un empresario para la aceptación.
- Revisión legal antes de cualquier publicación.

## Plan de implementación

### Secuencia

| Orden | Historia | Razón |
|---:|---|---|
| 1 | S42.1 | Revela primero si el producto realmente puede completar el viaje. |
| 2 | S42.2 | Con el viaje visible, se puede auditar qué skills participaron y cuáles faltan. |
| 3 | S42.3 | Después del camino feliz se prueban fallas y recuperación. |
| 4 | S42.4 | El catálogo solo puede escribirse cuando existe la verdad completa. |

### Hitos

| Hito | Historias | Evidencia de éxito |
|---|---|---|
| M1 — Primer viaje | S42.1 | Una empresa de prueba completa el recorrido en la primera plataforma. |
| M2 — Matriz e inventario | S42.1, S42.2 | macOS/Windows y skills tienen evidencia actual. |
| M3 — Producto seguro | S42.3 | Los escenarios negativos fallan de forma recuperable. |
| M4 — Verdad comercial | S42.4 | Catálogo, PDF, auditoría y aceptación humana coinciden. |

### Ruta crítica

S42.1 → S42.2 → S42.3 → S42.4.

S42.2 y la preparación de escenarios de S42.3 pueden avanzar en paralelo
después del primer recorrido, pero ambos deben cerrar antes del catálogo final.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---:|---|
| Confundir simulación con aceptación de hardware | Alto | Etiquetar plataforma, entorno y persona que aceptó. |
| Corregir funcionalidades durante la qualification | Alto | Registrar el defecto; reparar en una historia separada antes de repetir. |
| Crear un catálogo comercial más optimista que la evidencia | Alto | Cada afirmación debe enlazar a requisito y recibo. |
| No conseguir Windows limpio o empresario disponible | Alto | E42 permanece abierta; no fabricar aceptación. |
| Incluir datos reales en evidencia versionada | Alto | Fixtures o evidencia redactada y revisión antes de commit. |
| Sobrecargar al empresario con tecnicismos | Medio | Prueba de lectura y explicación en lenguaje de negocio. |

## Fuera de alcance

- Reflexión agentic y planificación automática → E43.
- Aprendizaje de resultados → E44.
- Equipos multi-agente → E45.
- Auto-mejora gobernada → E46.
- Publicación pública sin gate legal y autorización expresa.
