# Epic Retrospective: E18 — Class-to-Skill Learning Loop

**Date closed:** 2026-06-02
**Stories:** 4 (S18.1–S18.4)
**Total tests:** 45 passing
**Artifacts:** 6 coaching modules, 28 story artifacts, 1 report pipeline

## Objective

Transformar clases, transcripts y prompts docentes en un flujo que detecta patrones, decisiones y mejoras concretas para los skills del agente Escala.

## Was Objective Achieved?

Sí. La pipeline end-to-end funciona:

1. **S18.1** — `ingest_class()` crea un ClassBundle con metadatos, transcript, y artefactos
2. **S18.2** — `extract_patterns()` extrae temas (n-gramas), decisiones (keywords) y compromisos (regex)
3. **S18.3** — `suggest_deltas()` mapea patrones a skills específicos con 8 reglas de mapeo
4. **S18.4** — `generate_report()` produce report.md legible con 3 secciones: Summary, Patterns, Deltas

## Scope Delivered

| In Scope Item | Status | Evidence |
|---------------|--------|----------|
| Ingesta de transcript y materiales | ✔ | `class_intake.py` → bundle.yaml |
| Extracción de patrones | ✔ | `pattern_extraction.py` → patterns.json |
| Detección de mejoras por skill | ✔ | `skill_deltas.py` → deltas.json |
| Mapeo clase → skill → cambio sugerido | ✔ | 8 mapping rules, priority-sorted |
| Formato revisable | ✔ | `class_report.py` → report.md |

## Done Criteria

- [x] Cada clase nueva produce reporte reusable
- [x] Reporte muestra patrones, decisiones y oportunidades
- [x] Cada sugerencia apunta a un skill específico
- [x] Trazabilidad hacia la clase fuente

## What Went Well

- **Pipeline completa en un día:** 4 stories diseñadas, implementadas y mergadas en secuencia continua
- **45 tests pasando** sin fallos pre-existentes
- **Zero dependencias externas pesadas:** solo pyyaml como única dependencia nueva
- **Arquitectura limpia:** cada módulo tiene una responsabilidad única, los datos fluyen en una dirección

## What Could Be Better

- **Theme detection es básica:** solo n-gram frequency, sin semántica. Suficiente para V1, pero S18.2 se beneficiaría de embeddings o LLM ligero en V2
- **Mapping rules hardcodeadas:** deberían ser configurables vía YAML en una iteración futura
- **Contradiction detection no implementada:** quedó fuera del scope de S18.2

## Patterns Identified

- Pipeline lineal (bundle → patterns → deltas → report) es correcta para V1
- NFKD normalization para slugs con acentos
- Test isolation con `request.node.name` en fixtures
- N-gram frequency con stopwords preservadas para mantener adyacencia

## Metrics

| Metric | Value |
|--------|-------|
| Stories | 4 (M, M, L, S) |
| Commits | 8 (2 per story) |
| Tests | 45 |
| Modules | 6 (3 core + 3 test) |
| LOC (core) | ~680 |
| LOC (tests) | ~470 |

## Lessons for Next Epic

1. Mantener la secuencia lineal para pipelines de datos — funcionó bien
2. Usar `request.node.name` para fixtures de tests desde el inicio
3. Separar facts/interpretations/suggestions en reportes — evita mezclar intención docente con de producto

## Tag

`epic/e18-complete`
