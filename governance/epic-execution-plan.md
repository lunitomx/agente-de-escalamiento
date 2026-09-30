# Plan de ejecución canónico — ESCALA

> **Actualizado:** 2026-09-12
> **Propósito:** cerrar la meta de producto con verdad verificable, sin convertir
> herramientas internas ni aprobaciones rutinarias en bloqueos artificiales.

## Punto de partida verificado

- La auditoría 2026-09-12 abre E78–E81 como reparación y calificación prioritaria
  del piloto. [Programa y evidencia](pilot-readiness-2026-09-12.md). Son 24
  historias planificadas; no hay implementación ni participantes ejecutados.
- E41 se reabre por H05: `healthy` por marker no demuestra runtime vivo. E78
  posee la implementación correctiva; E41 conserva su recualificación.
- E43 está completa localmente: seis historias mergeadas y **135 pruebas
  focalizadas actuales** pasan. E42 es su gate externo de release, no una razón
  para rehacerla.
- E49, E52, E55 y E56 están completas y son contratos que se pueden consumir.
- E10 reparó S10.10 y S10.11 localmente: el export portable ya no depende
  del checkout y el instalador exige plataforma explícita, usa `.venv` mediante
  `uv` y no configura MCPs por detección incidental. E78 repara ahora el
  lanzador y update que no respetan ese contrato; E42/E68 conservan la
  aceptación externa en hardware limpio y con modelos reales.
- El conteo histórico de aceptación maestra era 36/42; E42 conserva sus seis
  requisitos externos pendientes y E41 debe recualificar los requisitos
  afectados por la regresión actual. No se presenta ese conteo como aceptación
  vigente del runtime reparado.
- E76 está completa: contrato RaiSE mínimo, grafo y retrospectiva reproducibles.
  Sus warnings opcionales no bloquean ninguna capacidad empresarial.
- La propuesta arquitectónica entregada por el dueño permanece archivada en
  [`notes/scaleup-operating-agent-completion-audit.md`](notes/scaleup-operating-agent-completion-audit.md).
  Se audita sólo al cierre total de esta meta, como fue solicitado.

## Reglas de operación RaiSE

Para cada épica nueva se usará el ciclo instalado, con delegación **AUTO** para
trabajo reversible y estrictamente dentro de scope:

```text
rai-session-start (una vez por sesión)
→ rai-epic-run E{n}
  → rai-epic-start → rai-epic-design → rai-architecture-review → rai-epic-plan
  → una sesión limpia por historia: rai-story-run S{n}.{m}
  → rai-epic-close
```

`rai-story-run` ejecuta en orden diseño, plan, implementación, arquitectura,
calidad, revisión y cierre. Toda historia exige prueba positiva y negativa,
procedencia de datos, documentación de uso y retrospectiva. Los gates técnicos
(`pytest`, `pyright`, `ruff check`, `ruff format --check`) detienen sólo la
historia afectada; el resto de carriles continúa.

Sólo se pide dirección humana cuando cambie materialmente el alcance, se vaya a
publicar/distribuir, se use una cuenta/conector externo, se conserve información
delicada sin consentimiento, se haga una acción destructiva o falle un gate. No
se pide autorización para decisiones técnicas reversibles dentro de esta meta.

Si la apertura de sesión RaiSE sigue incompleta, se registra en E76 y se sigue
el mismo ciclo mediante los artefactos versionados de `work/epics/`; no se
fabrica estado RaiSE ni se bloquea producto.

## Carriles y orden real

El siguiente carril de reparación tiene prioridad para la invitación del piloto:

```text
E78 instalación/runtime/recuperación ──┐
E79 aislamiento/seguridad/privacidad ──┼→ E80 integración → E81: 3–5 → 20
E80 semántica/intake ─────────────────┘
E42 y E68 aportan evidencia real por versión/plataforma; E70 decide distribución.
```

El [programa](pilot-readiness-2026-09-12.md) desglosa dependencias por historia;
E80 puede iniciar semántica mientras espera contratos de datos para integrar.
El resto de carriles permanece vigente y no autoriza saltar las reparaciones:

```text
Carril de distribución: E10/E41 → E78 reparación → E42 (hardware/aceptación) ────┐
Carril de producto:     E43 ✓ → E44 (en curso) → E45 (en curso) ─────────────────────────────┤
Carril de conocimiento:          E57 ✓ → E58 ✓ → E59 ✓ → E60..E63 (en curso) → E64 → E65 ──────┤
                                                                            ↓
Portabilidad:                                                           E67 → E68 → E69
                                                              ↓
Extensiones:                                      E71 / E72 / E73 / E74 / E75 / E77
                                                              ↓
Release:                                                    E70

En paralelo, sin bloquear desarrollo: E42 (pruebas externas) y E76 (RaiSE).
E46 se alimenta de resultados reales de E44/E45; nunca cambia producto solo.
```

## Backlog ejecutable por épica

| Carril | Épica | Scope de trabajo | Handoff / dependencia real | Gate de cierre honesto |
|---|---|---|---|---|
| Reparación | E78 | Intérprete único, bundle íntegro, actualización efectiva, proceso real y backup/restauración. | S78.1 es diseñable; contratos existentes E10/E41 son entrada, no bloqueos circulares. | Se ejecuta comportamiento de V1/V2/rollback y lectura/escritura reales. |
| Reparación | E79 | Empresa activa, aislamiento completo, migración, HTTP y explicación de datos/modelo. | Contrato/HTTP diseñables; migración consume S78.5; E74 reutiliza el resultado. | Cero cruces y filtraciones; origen, archivos y consentimiento verificados. |
| Reparación | E80 | Semántica de indicadores, contexto, PDF textual/fallback y continuidad. | Semántica diseñable; integración consume E78/E79; E73 reutiliza el contrato. | Placeholders no equivalen a salud; acción sustentada y reanudación coherentes. |
| Piloto | E81 | Protocolo/soporte → 3–5 acompañados → 20 independientes → decisión. | Preparación posible; ejecución espera E78–E80 y evidencia real aplicable E42/E68. | Métricas con denominador/asistencia, cero incidentes críticos y decisión humana. |
| Recualificación | E41 | Revalidar requisitos de runtime/lifecycle tras la regresión H05. | Implementación delegada exclusivamente a E78. | Recibos reales sustituyen la suficiencia del marker, sin borrar historia. |
| Externo | E42 | Ejecutar la aceptación maestra que falta: macOS/Windows limpios, invocación de skills, inventario/PDF y aceptación de dueño. | Corre paralela a todas las épicas. | 42/42 requisitos con recibos reproducibles y aprobación humana; no se sustituyen por fixtures. |
| Operación | E76 | Restaurar manifest/configuración/grafo de RaiSE sin tocar memoria de empresa. | Paralelo; requiere consentimiento explícito antes de una inicialización forzada. | `rai doctor` limpio en lo aplicable y entorno reproducible sin venv duplicado. |
| Producto | E44 | Decisión → acción → seguimiento → resultado → aprendizaje confirmado → cockpit. | Consume E43 completa; E42 sólo para release. | Los cuatro pilares tienen ciclos calificados, el dueño confirma/corrige aprendizaje y no hay causalidad inventada. |
| Producto | E45 | Un orquestador visible que llama especialistas privados Cash, Execution, People y Strategy cuando aportan valor. | Después de E44 y contratos E49/E55. | Un solo diálogo público, delegación mínima, desacuerdos explícitos y casos simples sin sobre-orquestación. |
| Fuente | E57 | Manifiesto de fuente, límites de autoridad, procedencia y mapa de cobertura del corpus permitido. | Puede iniciar ya; usa estado local/privado. | Cada unidad tiene locator, hash, tipo y limitación de licencia/uso. |
| Modelo | E58 | Schema v2, procedencia, aliases, revisión, migración y vistas derivadas. | Consume E57 y absorbe la reconciliación pendiente de E6 mediante S58.3. | Mapa de todos los IDs E6 a v2 o disposición explícita; ningún consumidor roto ni segunda fuente de verdad. |
| Fidelidad | E59 | Fundamentos 4D, barreras, disciplinas y decisiones con evidencia literal. | Después de E58. | Nodos, reglas y negativas aprobados por verificador independiente. |
| Fidelidad | E60 | Corpus People: FACe/PACe/OPPP y límites de People. | Después de E58; paralelo con E59/E61–E63. | Cobertura trazable, no inventa evaluaciones de personas. |
| Fidelidad | E61 | Corpus Strategy: core, siete estratos, SWT, visión y customer journey. | Después de E58; paralelo. | Cada procedimiento conserva evidencia, condiciones y huecos externos. |
| Fidelidad | E62 | Corpus Execution: prioridades, meeting rhythm, hábitos y feedback loops. | Después de E58; paralelo. | Ritmos y compromisos generan responsables, fecha y métricas sin automatizar imposiciones. |
| Fidelidad | E63 | Corpus Cash: CASh, CCC, Power of One y los ejercicios del Learning Day. | Después de E58; paralelo. | Fórmulas/periodos verificables, conciliación de entradas y ninguna cifra inventada. |
| Consolidación | E64 | Resolver candidatos, conflictos, relaciones, cobertura y cola de revisión. | Requiere E59–E63. | Cobertura de estructuras nombradas, 100% de reglas normativas con evidencia y cero relaciones rotas. |
| Procedimientos | E65 | Compilar los seis procedimientos MVP desde nodos verificados; no desde texto crudo. | Requiere E64, E49 y E52. | Cada procedimiento tiene trigger/no-trigger, entrevista, salida, aceptación, memoria y evaluación. |
| Portabilidad | E67 | Empaquetar núcleo de skills y cuatro especialistas internos con adaptadores aislados Codex/Claude, incluido paquete Agent Plugins v1 sin ampliar la superficie pública. | Requiere E45, E65 y E56. | Mismo núcleo portable, una puerta `escala`, manifest estándar y adaptadores sin mezclar instrucciones de plataforma. |
| Calificación | E68 | Probar equivalencia semántica en Codex y Claude con sesiones limpias. | Requiere E67 y E35. | Activación, no-activación y golden cases equivalentes; diferencias reportadas, no ocultas. |
| Biblioteca | E69 | Entregar el resto de procedimientos por olas, no todos de golpe. | Requiere E68. | Cada ola pasa cobertura, evidencia, activación y aceptación antes de abrir la siguiente. |
| Extensión | E75 | Diagnóstico narrativo y deep dive elegido por el empresario, nunca una batería 1–5. | S75.1/S75.2 consumen E49/E55; los handoffs S75.3–S75.5 esperan E65. | Handoff explicable hacia People/Strategy/Execution/Cash y preguntas que piden evidencia sólo cuando cambian la decisión. |
| Extensión | E71 | Research de mercado, tamaño, competidores, prospectos e investigación fechada. | Requiere E49, E55 y E67. | Fuentes, fecha, nivel de confianza, confirmación del dueño y límites de investigación visibles. |
| Extensión | E72 | Cash Learning Day y plantilla financiera: carga, reconciliación, facilitación y decisión de 90 días. | Requiere E38, E55, E63, E65 y E67. | Artefacto de Cash usable, cifras trazables, huecos explícitos y plan Who/What/When. |
| Extensión | E73 | Asesor de dashboards que propone el panel correcto cuando existe evidencia. | Requiere E38, E40, E55, E65, E67 y semántica E80. | No recomienda ni grafica métricas inexistentes; entrega definición de dato, periodo y decisión soportada. |
| Extensión | E74 | Workspace compartido/multiempresa: Markdown/YAML compartido, SQLite sólo caché local. | Requiere E37, E52, E55, E67 y aislamiento E79; no duplica el resolver. | Aislamiento por empresa, conflictos explícitos y jamás sincronización de SQLite como autoridad. |
| Extensión | E77 | Biblioteca privada de cursos: fuente autorizada → candidatos revisados → pack local bajo ESCALA. | Requiere E57/E58, E65, E67 y E68; coordina con E69/E71/E75. | Procedencia, derechos, privacidad, no-activación y retiro verificables; nunca contenido crudo en distribución. |
| Aprendizaje | E46 | Mejora gobernada desde señales aprobadas de uso/resultados, no auto-mutación. | Tras E44/E45 y feedback suficiente. | Hipótesis, evaluación A/B o equivalente, aprobación y rollback; cambios nunca automáticos. |
| Release | E70 | Validación, instalación y distribución completa y honesta. | Requiere E42, E68, E69, E71–E75 y decisión/evidencia E81. | Instalación limpia, paridad cross-platform, límites de IP/privacidad claros y aceptación final. |

## Primeras ejecuciones sin espera

**Prioridad del piloto desde 2026-09-12:** diseñar S78.1, S79.1/S79.4 y S80.1;
preparar S81.1. La invitación espera los gates del programa. El orden siguiente
describe los carriles anteriores, que pueden continuar sin sustituir esa prioridad.

1. **E75** inicia S75.1/S75.2: assessment narrativo, evidencia y confirmación; los handoffs a procedimientos permanecen bloqueados por E65.
2. **E44/E45** continúan únicamente hacia evidencia empresarial: retrospectiva,
   aceptación y comparación real, no más sustitutos sintéticos.
3. **E60–E62** cierran sólo la inspección visual autorizada de formularios; sus
   inventarios, fidelidad y validadores ya están terminados técnicamente.
4. **E63** mantiene CASh como herramienta *source-bounded*: no atribuye ni
   compila fórmulas externas; sólo avanza candidatos que tengan evidencia
   autorizada y revisión independiente.
5. Tras esos gates, **E64** consolida únicamente candidatos aprobados y habilita
   **E65**, después **E67/E68**.
6. **E42** recoge pruebas externas durante todo el programa. **E76** está
   completa y se reabre sólo ante una regresión reproducible propia.

## Evidencia y cierre transversal

Cada commit de historia debe enlazar el artefacto de scope/PRD, prueba, recibo
u resultado verificable, decisión de seguridad/datos y retrospectiva. Ninguna
épica se cierra porque el título diga `done`, porque exista una rama antigua o
porque un test sintético esté verde: se compara el scope contra evidencia actual.

Al terminar E70 y E42, se ejecutará la auditoría final de la nota arquitectónica
archivada para responder exactamente qué se incorporó, qué falta y qué requiere
una nueva épica. Hasta entonces no se declara completada esta meta global.
