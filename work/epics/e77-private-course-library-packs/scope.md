---
epic_id: E77
title: Biblioteca privada de cursos y packs instalables
status: planned
depends_on: [E57, E58, E65, E67, E68]
related: [E69, E71, E75]
closure_disposition: active
---

# Scope E77

## Objetivo

Permitir que un dueño aporte cursos que tiene derecho a usar y los convierta,
en su instalación local, en paquetes de conocimiento y procedimientos
internos. ESCALA conserva una única puerta pública y separa con rigor fuente,
interpretación, datos externos y estado de empresa.

## Contrato de una fuente de curso

Antes de extraer cualquier capacidad, el sistema debe registrar localmente:

- título, autor/instructor, fecha, formato y propietario;
- permiso o restricción de uso, distribución y retención;
- hash y localizador del archivo original; para video/audio, timestamps;
- calidad de captura: original, OCR, transcripción revisada o transcripción
  ruidosa;
- clasificación de cada unidad: source-explicit, source-synthesis,
  historical-example, external-reference, company-local o model-hypothesis;
- estado: candidato, aprobado para uso local, retirado o bloqueado.

Una transcripción sin timestamps ni revisión humana puede producir candidatos,
pero no reglas, fórmulas, citas, afirmaciones normativas ni un pack instalable.

## Dentro

- Ingesta local y consentida de curso, transcript, slides, workbook o notas.
- Manifiesto, procedencia, segmentación y cola de revisión por curso.
- Compilación de candidatos aprobados al mismo contrato de procedimiento E65.
- Packs privados con SKILL.md interno, referencias, assets y evals locales.
- Activación bajo demanda por ESCALA, sin un comando público adicional.
- Conflictos visibles entre cursos, metodología base, research externo e
  información confirmada de empresa.
- Instalación, actualización, desactivación y eliminación explícitas del pack,
  sin sincronizar SQLite ni publicar contenido crudo.
- Evals de activación, no-activación, procedencia, IP, privacidad y regresión.

## Fuera

- Guardar contenido de cursos en Git, en el export público o en un plugin
  compartido por defecto.
- Extraer material cuyo permiso es desconocido o que el dueño no autorizó.
- Usar un resumen de clase como evidencia de mercado, salud, legal, finanzas,
  psicología o desempeño personal.
- Convertir ejemplos del instructor, marcas, clientes o anécdotas en reglas.
- Reemplazar E71: el pack puede formular una hipótesis de mercado, pero E71
  sigue siendo responsable de fuentes externas fechadas, TAM/SAM/SOM y
  competidores.
- Reemplazar E69: los procedimientos de Scaling Up siguen su ola fuente y
  fidelidad propia.

## Historias y secuencia

| Orden | Historia | Entrega verificable | Dependencia |
|---:|---|---|---|
| 1 | S77.1 Contrato de fuente y derechos | Schema local, consentimiento, hash, retención y bloqueo fail-closed. | E57, E58 |
| 2 | S77.2 Curación y revisión | Manifiesto, unidades, candidatos, evidencia y cola de ambigüedades. | S77.1 |
| 3 | S77.3 Contrato de pack privado | Layout local, lifecycle, activación/desactivación y límites de export. | S77.1, E67 |
| 4 | S77.4 Compilador de capacidades | Candidatos aprobados → procedimientos E65 → capacidades internas. | S77.2, E65 |
| 5 | S77.5 Piloto BlackSeller | Pack local de ventas con evaluación humana y sin promover contenido incierto. | S77.2–S77.4 |
| 6 | S77.6 Evals, conflicto y portabilidad | Casos positivos/negativos, aislamiento de datos y paridad Codex/Claude. | S77.3–S77.5, E68 |

## Caso de diseño: BlackSeller

El material recibido el 2026-08-29 es una transcripción de una sesión llamada
BlackSeller. Por ahora es una fuente candidata privada: no contiene
timestamps, permiso de distribución, archivo original verificable ni revisión
de transcripción. Se conserva sólo este análisis, no el texto recibido.

### Candidatos de trabajo, no capacidades promocionadas

| Candidato | Valor empresarial | Entregable posible | Límite |
|---|---|---|---|
| Mapa producto → resultado | Reencuadrar una oferta en impacto del cliente. | Hipótesis de valor por segmento. | Requiere confirmación de cliente; no promete ROI. |
| Comité de compra y personajes | Diferenciar usuario, influenciador, comprador y operador. | Mapa de stakeholders y mensajes por hipótesis. | No perfila personas ni inventa motivaciones. |
| Mercado y oportunidad | Formular supuestos sobre tamaño, segmentos y participación. | Brief de preguntas, rango y supuestos. | E71 verifica datos, fuentes y competidores. |
| Diferenciación y oferta complementaria | Identificar valor agregado, servicio y prueba. | Experimento de oferta de 90 días. | No recomienda descuentos ni pricing sin evidencia. |
| Funnel y capacidad comercial | Relacionar meta, ticket, conversión, actividad y capacidad. | Modelo editable con unidades y supuestos. | Datos de empresa se confirman; no se copian cifras de clase. |
| Descubrimiento y práctica de pitch | Preparar una conversación por problema, rol y evidencia. | Guion de descubrimiento y ensayo. | No usa manipulación, afirmaciones médicas/psicológicas ni cierres engañosos. |

### Material que permanece bloqueado o como referencia externa

- La regla 80/20, libros citados, PNL, salud personal, motivación, Pareto,
  Sun Tzu y metodologías ajenas son referencias externas, no conocimiento
  completo del pack.
- Anécdotas de ventas, marcas, cifras, estudios de caso y recomendaciones del
  instructor quedan como ejemplos históricos o hipótesis.
- Cualquier afirmación sobre seguridad, medicina, patrimonio, retorno,
  demencia, riqueza o desempeño se bloquea hasta una fuente adecuada y el
  límite de uso correspondiente.

## Criterios de terminación

- Ningún curso sin permiso y procedencia local pasa de candidato a pack.
- Todo procedimiento promovido tiene trigger, non-trigger, preguntas,
  decisiones, salida, criterios de aceptación, actualización de estado y evals.
- El empresario no ve comandos técnicos ni necesita elegir mini-agentes.
- El paquete declara qué sabe, qué no sabe, qué viene de la fuente y qué debe
  validarse con datos de su empresa o research externo.
- Contenido crudo, archivos privados, credenciales y SQLite quedan fuera de
  Git, export público, Agent Plugin y carpetas sincronizadas por defecto.
- BlackSeller obtiene una decisión de revisión humana: promover una capacidad,
  corregirla, mantenerla como borrador o retirarla.
- La instalación y retiro de un pack preservan la memoria aprobada de empresa.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Curso convincente pero transcripción errónea | timestamps, hash, revisión independiente y cola de ambigüedades. |
| Infracción de derechos o filtración de contenido | local-only por defecto, permiso explícito y exclusión fail-closed del export. |
| Curso contradice metodología o datos de empresa | procedencia visible, conflicto explícito y confirmación humana. |
| Proliferación de mini bots | una puerta pública; packs son capacidades internas bajo demanda. |
| Consejos de alto riesgo | limitar a hipótesis/ejercicios y exigir fuentes o profesional competente. |

## Plan de ejecución RaiSE

~~~text
rai-session-start
→ rai-epic-run E77
  → S77.1 source/rights contract
  → S77.2 curate + independent fidelity review
  → S77.3 private pack lifecycle
  → S77.4 compile verified procedures
  → S77.5 BlackSeller pilot
  → S77.6 cross-platform + privacy evals
→ rai-epic-close
~~~

Cada historia requiere diseño, prueba positiva/negativa, revisión independiente,
recibo de privacidad y retrospectiva. El material del curso nunca se adjunta a
un commit ni a una salida de diagnóstico.


## Implementation Plan

> Added by RaiSE epic planning on 2026-08-30. The design artifact is absent
> because E77 was initialized as a governed planning epic; this plan uses the
> existing scope/PRD and local graph queries, which returned no additional
> patterns. It does not waive any hard dependency.

### Story Sequence

| Order | Story | Size | Dependencies | Milestone | Rationale |
|:-----:|-------|:----:|--------------|-----------|-----------|
| 1 | S77.1 — Contrato de fuente y derechos | M | E57, E58 ✓ | M1 | Establishes the irreversible privacy/IP boundary before any extraction or local storage. |
| 2 | S77.2 — Curación y revisión | M | S77.1 | M1 | Produces candidates and ambiguity queue without compiling or exposing course content. |
| 3 | S77.3 — Contrato de pack privado | M | S77.1, E67 | M2 | Makes pack lifecycle compatible with the canonical capability map rather than creating a parallel skill system. |
| 4 | S77.4 — Compilador de capacidades | L | S77.2, E65 | M2 | Reuses the approved procedure contract; raw course fragments can never directly become a capability. |
| 5 | S77.5 — Piloto BlackSeller | M | S77.2–S77.4, source permission, original/timestamps | M3 | Validates one bounded sales pack with human review before generalizing the system. |
| 6 | S77.6 — Evals, conflicto y portabilidad | L | S77.3–S77.5, E68 | M4 | Demonstrates no-activation, conflict, privacy and Codex/Claude semantic parity before epic close. |

### Milestones

| Milestone | Stories | Target | Success Criteria |
|-----------|---------|--------|------------------|
| **M1: Private source skeleton** | S77.1, S77.2 | After review approval | Authorized local source produces only attributable candidates, gaps and a review queue; no raw course data enters Git/export. |
| **M2: Safe compilation path** | S77.3, S77.4 | After E65/E67 complete | Pack lifecycle and procedure compiler share canonical contracts; invalid, unlicensed or unapproved candidates fail closed. |
| **M3: BlackSeller pilot** | S77.5 | After M2 + source proof | One owner approves a bounded sales exercise; claims remain scoped and artifacts preserve provenance. |
| **M4: Epic complete** | S77.6 | After E68 complete | Privacy, activation/no-activation, conflict and cross-platform evals pass; retrospective confirms no raw-content leakage. |

### Parallel Work Streams

```text
Critical: S77.1 ──► S77.2 ───────────────► S77.5 ──► S77.6
                      │                       ▲
E67 gate:              └──► S77.3 ───────────┤
E65 gate:              └──► S77.4 ───────────┘
E68 gate:                                      └──► S77.6
```

**Merge points:** S77.1 is the privacy/IP gate. S77.3 and S77.4 may proceed
in parallel only after their respective upstream epics close. S77.5 joins both;
S77.6 cannot start before the BlackSeller pilot and E68 qualification.

### Progress Tracking

| Story | Size | Status | Actual | Velocity | Notes |
|-------|:----:|:------:|:------:|:--------:|-------|
| S77.1 | M | Ready after review | — | — | E57/E58 complete; no course source is needed to build the generic fail-closed contract. |
| S77.2 | M | Pending | — | — | Starts only after S77.1; BlackSeller remains a candidate without raw content in repository. |
| S77.3 | M | Blocked | — | — | Hard dependency: E67 capability/adapters are planned. |
| S77.4 | L | Blocked | — | — | Hard dependency: E65 procedure compiler is planned. |
| S77.5 | M | Blocked | — | — | Needs S77.4 plus explicit rights, original asset/hash and timestamps/review for BlackSeller. |
| S77.6 | L | Blocked | — | — | Hard dependency: E68 semantic cross-platform qualification is planned. |

### Sequencing Risks

| Risk | L/I | Mitigation |
|------|:---:|------------|
| Course material leaks through test fixtures or export | H/H | S77.1 blocks storage/export before extraction; tests use synthetic fixtures only. |
| A generic pack duplicates E65/E67 behavior | M/H | S77.3/S77.4 consume canonical maps/contracts; no independent router or public command. |
| BlackSeller transcript is inaccurate or unlicensed | H/H | Keep it candidate-only until permission, source hash and review evidence exist. |
| The team treats a trainer claim as business evidence | M/H | Origin labels, explicit conflict view and E71 handoff for external market facts. |
