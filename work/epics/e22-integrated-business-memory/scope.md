# Epic Scope: E22 — Memoria Empresarial Integrada

**Status:** In progress — S22.3 complete
**Dependencies:** E10 (distribución), E18 (SQLite, memoria, grafo y sesiones)
**Audited:** 2026-08-26
**Tamaño:** L

## Outcome

Entregar un ScaleUp local-first con una sola memoria empresarial por proyecto.
La conversación pública debe recuperar contexto relevante al empezar y guardar
hechos, decisiones y aprendizajes confirmados al cerrar, sin exponer comandos,
skills, rutas ni la arquitectura al empresario.

## In Scope

- Contrato versionado de memoria: hechos, decisiones, aprendizajes, entidades,
  relaciones, fuente, fecha, confianza, conflicto y confirmación.
- Decisión explícita de fuente de verdad SQLite y compatibilidad/migración de
  los YAML actuales: perfil, conversación, plan y worksheets.
- Distribución del runtime necesario de E18 desde install.sh para Claude, Codex
  y Hermes, sin servicio externo ni dependencia de plugin.
- Base SQLite local por proyecto, con creación, health check, backup/restore y
  migración idempotente.
- Inicio de sesión: recuperar perfil, últimos cambios y facts relevantes con
  degradación segura si aún no hay datos.
- Cierre/pausa de sesión: proponer y guardar sólo hechos, decisiones o patrones
  autorizados por la persona; registrar proveniencia.
- Integración de inicio/cierre y recuperación en el front door público sin
  romper onboarding, diagnóstico, plan ni progreso actuales.
- Tests unitarios, de migración, integración y cliente real desde instalación
  limpia; actualización de documentación de privacidad y rollback.

## Out of Scope

- Cloud, sincronización entre dispositivos, multiusuario, CRM o telemetría.
- Plugin Holographic, vector database, embeddings o búsqueda semántica neural
  hasta que una evaluación pruebe que SQLite/índices deterministas no bastan.
- Guardar automáticamente inferencias del modelo como hechos de empresa.
- Rediseñar todos los dashboards E14–E17 antes de cerrar la fuente única.
- Board sintético E21, fuentes nuevas de conocimiento o recomendaciones
  financieras/legales.

## Reglas no negociables

1. Los datos empresariales permanecen locales y visibles/exportables para la
   empresa.
2. Ninguna inferencia se convierte en hecho sin fuente y confirmación definida.
3. SQLite no puede coexistir indefinidamente como copia divergente del YAML.
4. Migración, actualización, desinstalación y rollback deben preservar datos.
5. La persona sigue usando lenguaje natural; la memoria no añade comandos ni
   jerga al recorrido público.
6. Sin memoria disponible, ScaleUp degrada al flujo actual sin bloquear a la
   persona ni inventar contexto.

## Historias propuestas

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S22.1 — Contrato y ADR de memoria | M | Esquemas, privacidad, confirmación y fuente única definidos. |
| 2 | S22.2 — Runtime, instalación y ciclo SQLite ✓ | L | E18 se distribuye, crea/valida base por proyecto y permite rollback. |
| 3 | S22.3 — Migración YAML idempotente ✓ | L | Perfil, diagnóstico, plan y worksheets migran sin pérdida ni duplicados. |
| 4 | S22.4 — Inicio y recuperación contextual | M | Sesión nueva recupera facts, cambios y foco relevante. |
| 5 | S22.5 — Cierre, hechos y patrones confirmados | L | Decisiones/aprendizajes con fuente, confianza y confirmación. |
| 6 | S22.6 — Front door y continuidad natural | M | ScaleUp orquesta memoria sin exponer infraestructura. |
| 7 | S22.7 — Validación E2E, privacidad y release | M | Matriz cliente, backup/restore, regresiones y docs verdes. |

## Acceptance Criteria

- [ ] Una instalación limpia contiene el runtime de memoria esperado en cada
  plataforma soportada y no instala datos de empresa compartidos globalmente.
- [ ] La migración se puede repetir y conserva todos los artefactos actuales.
- [ ] La conversación nueva recupera información relevante verificable desde la
  base, aun sin historial de chat.
- [ ] Hechos y decisiones muestran su fuente; las inferencias no confirmadas se
  distinguen o se descartan.
- [ ] Cambios, contradicciones y confianza siguen una política documentada.
- [ ] Fallo o ausencia de SQLite degrada con seguridad al flujo actual.
- [ ] Instalar → conversar → cerrar → abrir sesión nueva → recuperar pasa en
  Claude Code y Codex; Hermes obtiene cobertura equivalente o un límite explícito.
- [ ] Suite completa, smoke real, backup/restore y desinstalación pasan antes del
  cierre.

## Gates Before Implementation

- [ ] ADR aprobado: ubicación de base, esquema, confirmación y retención.
- [ ] Política de migración/rollback aprobada con fixture de empresa existente.
- [ ] Contrato de memoria y casos adversariales escritos antes de tocar el front
  door.
- [x] Diagnóstico RaiSE M documentado localmente el 2026-08-26.
- [x] Base actual: 404 passed, 2 skipped (2026-08-24).

## Implementation Plan

La ruta crítica es S22.2 → S22.3 → S22.4 → S22.5 → S22.6 → S22.7. Se usa
riesgo primero: antes de modificar la conversación pública se prueba que el
runtime puede vivir, migrar y aislarse dentro de un proyecto real.

| Pos. | Story | Dependencias | Razonamiento y habilita | Estado | Real |
|:---:|---|---|---|:---:|:---:|
| 1 | S22.1 — Contrato y ADR | Ninguna | Fija fuente única, consentimiento y fixture adversarial; evita migrar datos ambiguos. | Done | — |
| 2 | S22.2 — Runtime, instalación y ciclo SQLite | S22.1 | Walking skeleton: prueba DB local, health, backup y rollback sin servidor ni defaults globales. Habilita todo lo demás. | Done | 2026-08-26 |
| 3 | S22.3 — Migración YAML idempotente | S22.2 | Lleva el estado existente a la fuente única y prueba repetición/recuperación antes de leerlo en conversación. | Done | 2026-08-26 |
| 4 | S22.4 — Inicio y recuperación contextual | S22.2, S22.3 | Recupera sólo datos confirmados y muestra degradación segura; valida el valor entre sesiones. | Blocked by S22.3 | — |
| 5 | S22.5 — Cierre, hechos y patrones confirmados | S22.2, S22.3 | Añade propuesta, sí/no, fuente y confianza. Puede desarrollarse en paralelo con S22.4 una vez migración esté estable. | Blocked by S22.3 | — |
| 6 | S22.6 — Front door y continuidad natural | S22.4, S22.5 | Conecta inicio/cierre sin exponer infraestructura y conserva onboarding, diagnóstico, plan y progreso. | Blocked by S22.4/S22.5 | — |
| 7 | S22.7 — Validación E2E, privacidad y release | S22.6 | Prueba instalación limpia → conversar → confirmar/cerrar → nueva sesión → recuperar en los clientes soportados. | Blocked by S22.6 | — |

No hay una oportunidad de paralelismo segura antes de S22.3: el contrato de
rutas y la migración definen los datos que consumirán inicio y cierre. Después
de S22.3, S22.4 y S22.5 pueden avanzar en módulos distintos; se integran en
S22.6.

## Milestones

| Hito | Historias | Criterio verificable | Demo |
|---|---|---|---|
| M1 — Walking skeleton | S22.1–S22.2 | Un proyecto temporal crea, valida, respalda y restaura `.scaleup/memory/escala.db`; ningún dato usa el directorio personal. | Ejecutar el bridge sobre una empresa vacía. |
| M2 — Memoria confiable | S22.3–S22.5 | Fixture legado migra dos veces sin duplicar; sesión nueva recupera datos confirmados; un candidato rechazado no se guarda. | Migrar, confirmar una decisión y recuperarla en otra sesión. |
| M3 — Integración E2E | S22.6 | Runtime instalado conserva el recorrido público y recupera contexto desde el front door. | Instalación limpia y conversación natural de continuidad. |
| M4 — Epic complete | S22.7 | Matriz Claude/Codex pasa, Hermes queda cubierto o limitado explícitamente; privacidad, rollback y regresiones verdes. | Flujo completo de empresa existente, de instalación a segunda sesión. |

### Gates de historia

- S22.2 no puede usar `~/.escala`, un servidor HTTP ni rutas implícitas.
- S22.3 necesita fixtures de perfil, conversación, plan y worksheet; dos
  corridas deben producir el mismo conteo de registros.
- S22.4/S22.5 deben tener tests de ausencia/corrupción de DB y de rechazo de
  candidato, respectivamente.
- S22.6 sólo se integra cuando ambos contratos se prueben de forma aislada.
- S22.7 usa infraestructura real de instalación; mocks no sustituyen el smoke
  de los artefactos copiados.

### Sequencing Risks

1. El runtime de E18 puede incluir dependencias o rutas globales ocultas; M1
   las detecta antes de tocar el front door.
2. Los YAML y Markdown actuales pueden codificar la misma información con
   nombres distintos; S22.3 conserva proveniencia y prueba idempotencia.
3. El texto natural puede crear datos falsos; S22.5 separa propuesta de
   persistencia y exige una respuesta afirmativa inequívoca.
