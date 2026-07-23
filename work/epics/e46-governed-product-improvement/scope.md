---
epic_id: "E46"
title: "Governed Product Improvement"
status: "planned"
depends_on: ["E42", "E43", "E44", "E45"]
supersedes: ["E24"]
created: "2026-07-23"
---

# E46 — Mejora gobernada del producto

## Objetivo

Crear un ciclo local y controlado que detecte problemas repetidos, prepare una
propuesta de mejora verificable, la pruebe contra casos conocidos y solo la
promueva tras aprobación humana explícita.

**Valor:** ESCALA mejora con el uso real sin que una empresa entregue sus datos
para entrenar a otra, y sin que una sugerencia del sistema se convierta sola en
un cambio de producto.

## Historias

| ID | Historia | Tamaño | Estado | Demostración de valor |
|---|---|:---:|:---:|---|
| S46.1 | Recibir señales seguras | M | Pending | Bug reports, resultados y clases entran con identidad y datos empresariales omitidos. |
| S46.2 | Distinguir patrón de anécdota | M | Pending | El sistema agrupa señales repetidas y conserva su evidencia redactada. |
| S46.3 | Preparar propuesta revisable | M | Pending | Una tarjeta explica problema, cambio, impacto esperado, límites y evidencia. |
| S46.4 | Probar antes y después | M | Pending | Casos positivos y negativos demuestran mejora sin regresión. |
| S46.5 | Aprobar, versionar y revertir | M | Pending | Un humano aprueba; el cambio tiene versión anterior y rollback probado. |
| S46.6 | Medir el ciclo completo | M | Pending | La señal disminuye después del cambio o se activa reversión. |

## S46.1 — Recibir señales seguras

Se unificarán tres entradas locales: reportes anónimos de bug/mejora, resultados
confirmados o rechazados de E44 y reportes de aprendizaje revisables de clases.

**Termina cuando:** cada señal declara consentimiento, omite identidad y datos
de empresa, y no genera envío automático por internet.

## S46.2 — Distinguir patrón de anécdota

Una señal aislada queda como observación. Solo señales repetidas, verificables o
de severidad alta se convierten en un problema candidato.

**Termina cuando:** el equipo puede rastrear por qué una propuesta existe sin
leer el contenido privado original.

## S46.3 — Preparar propuesta revisable

Cada propuesta contendrá problema, comportamiento afectado, evidencia redactada,
cambio sugerido, beneficio esperado, posibles daños, casos que debe superar y
estado: propuesta, aprobada, aplicada, rechazada o revertida.

**Termina cuando:** una persona responsable puede aprobar o rechazar sin tener
que reconstruir todo el historial técnico.

## S46.4 — Probar antes y después

Antes de aprobar, la propuesta se prueba con casos exitosos, negativos y de
regresión. La comparación debe mostrar qué mejora y qué no cambia.

**Termina cuando:** una propuesta que rompe un comportamiento protegido no llega
a aprobación humana como si fuera segura.

## S46.5 — Aprobar, versionar y revertir

La promoción requiere un humano identificado, una versión anterior, una
descripción corta de cambio y una reversión comprobada. La aprobación puede ser
rechazo o devolución para obtener mejor evidencia.

**Termina cuando:** no existe camino automático desde propuesta a cambio.

## S46.6 — Medir el ciclo completo

Después de aplicar una mejora aprobada, se mide si disminuye el problema
original. Si no mejora o provoca daño, se registra y se activa reversión o una
nueva investigación.

**Termina cuando:** una señal real recorre el camino completo y su resultado se
puede auditar.

## Dentro

- Señales locales, anonimizadas y revisables.
- Agrupación basada en repetición, severidad y evidencia.
- Propuesta, pruebas, aprobación, versión, reversión y medición.
- Reutilización de bugreport, E1801, E35 y el aprendizaje confirmado en E44.

## Fuera

- Telemetría central, entrenamiento de modelos o perfiles entre empresas.
- Auto-patch post-sesión o semanal de E24.
- Aplicación automática de cambios por cualquier agente.
- Publicación, despliegue o aviso externo automático.
- Tratamiento de datos empresariales como muestra de entrenamiento.

## Criterios de terminación

- [ ] Las señales no contienen identidad, datos de empresa o texto fuente sin
      consentimiento explícito.
- [ ] Un patrón candidato conserva evidencia redactada, severidad y repetición.
- [ ] Toda propuesta declara comportamiento, cambio, impacto, riesgos y casos.
- [ ] Los casos antes/después y regresiones pasan antes de solicitar aprobación.
- [ ] Un humano puede aprobar, rechazar o devolver la propuesta.
- [ ] Cada promoción tiene versión previa y rollback probado.
- [ ] No existe aplicación automática de cambios ni envío automático de datos.
- [ ] Un ciclo real demuestra reducción del problema o reversión documentada.
- [ ] Retrospectiva y auditoría de seguridad completadas.

## Dependencias

```text
E44 resultados confirmados ─┐
E45 valor de especialistas ─┼→ S46.1 señales → S46.2 patrón
Bugreport y E1801 ──────────┘                     ↓
                                      S46.3 propuesta → S46.4 pruebas
                                                           ↓
                                          S46.5 aprobación/reversión → S46.6 medir
```

- E44 cerrada con resultados y aprendizajes revisables.
- E45 cerrada o reducida según su gate de valor.
- Bugreport local y sus contratos de anonimato.
- Golden cases y gates de regresión existentes.
- Autoridad humana para aprobar o rechazar una propuesta.

## Plan de implementación

### Secuencia

| Orden | Historia | Razonamiento | Habilita |
|---:|---|---|---|
| 1 | S46.1 | La privacidad y la procedencia deben estar resueltas antes de leer patrones. | S46.2-S46.6 |
| 2 | S46.2 | Evita construir cambios sobre una anécdota. | S46.3 |
| 3 | S46.3 | Hace que la mejora sea una decisión revisable, no una sugerencia vaga. | S46.4-S46.5 |
| 4 | S46.4 | Los casos son la barrera antes de pedir autorización. | S46.5 |
| 5 | S46.5 | Garantiza control humano y reversibilidad. | S46.6 |
| 6 | S46.6 | Comprueba que la mejora resuelve el problema real. | Próximo ciclo o rollback |

### Hitos

| Hito | Historias | Criterio de éxito |
|---|---|---|
| M1 — Señal segura | S46.1-S46.2 | Una señal repetida se vuelve problema reproducible sin datos empresariales. |
| M2 — Propuesta comprobable | S46.3-S46.4 | Una mejora propuesta tiene evidencia y casos antes/después verdes. |
| M3 — Control humano | S46.5 | Una aprobación y reversión se ejercitan de extremo a extremo. |
| M4 — Mejora medida | S46.6 | Se demuestra reducción del problema o se documenta rollback. |

### Trabajo en paralelo

La preparación de fixtures para S46.4 puede avanzar mientras se construye S46.3,
pero ninguna propuesta pasa a aprobación sin la evidencia final de S46.4.

### Seguimiento

| Story | Estado | Evidencia esperada |
|---|---|---|
| S46.1 | Pending | Señales locales redacted y contrato de anonimato. |
| S46.2 | Pending | Patrón candidato con repetición y severidad. |
| S46.3 | Pending | Propuesta revisable con estados explícitos. |
| S46.4 | Pending | Comparativo antes/después y regresiones. |
| S46.5 | Pending | Aprobación humana, versión y rollback. |
| S46.6 | Pending | Medición posterior y auditoría. |

## Riesgos

| Riesgo | L/I | Mitigación |
|---|:---:|---|
| Una señal revela información de empresa | M/H | Redacción obligatoria, contrato fail-closed y revisión antes de promoción. |
| Cambiar por una anécdota | M/H | Repetición, severidad, evidencia y caso reproducible. |
| Una mejora rompe otro skill | M/H | Golden cases, casos negativos y gates antes de aprobación. |
| El sistema se autoaplica una mejora | L/H | Ninguna transición automática; aprobación humana y rollback obligatorio. |
| Confundir aceptación técnica con aceptación de producto | M/M | Medición posterior y criterio humano explícito. |

## Parking lot

- Portal central de feedback o entrenamiento compartido → rechazado hasta nueva
  decisión de producto, derechos de datos y cambio explícito del modelo local.
