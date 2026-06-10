# Auditoría de Repositorio — ScaliingUPAI (Escala Agent)

**Auditor:** Claude Fable 5 · **Fecha:** 2026-06-09 · **Branch:** `fix/auditoria-migracion`
**Repositorio:** `/Users/soyahuehuetedigital/Documents/GitHub/ScaliingUPAI desarrollo`

---

## Resumen Ejecutivo

**Calificación general de salud: B- (74/100)**

El motor de coaching Escala es un proyecto sólido en su núcleo — 510 tests, arquitectura en capas limpia, 80+ archivos de conocimiento declarativo, type annotations consistentes. Pero sufre de tres vicios que lo frenan:

1. **Infraestructura de calidad invisible:** 510 tests sin CI, dependencias no declaradas, cobertura no medida. La calidad existe en la cabeza del desarrollador, no en el sistema. Un clone limpio no sabe qué instalar.

2. **Código roto en paths no ejercitados:** `migrate.py` tiene 3 bugs de columnas inexistentes que nunca fallaron porque nunca se corrió contra el schema real. El parser YAML de 340 líneas no tiene un solo test.

3. **Sin defensa en runtime:** Los handlers HTTP no capturan excepciones — un JSON malformado crashea el worker. CORS completamente abierto.

**Top 3 riesgos:** (1) migrate.py roto — si alguien necesita re-ejecutar migración, falla silenciosamente, (2) sin CI — regresiones no detectadas hasta que un humano corre tests, (3) sin dependencias declaradas — conocimiento tribal necesario para desarrollar.

**Top 3 oportunidades:** (1) 510 tests YA escritos — solo falta automatizarlos, (2) arquitectura limpia que facilita refactors quirúrgicos, (3) 80+ YAMLs declarativos que ya marcan el camino correcto para extraer datos hardcodeados.

---

## 1. Mapa del Repositorio

**Propósito:** Agente de Escalamiento — motor de coaching AI que implementa Scaling Up (Verne Harnish). Guía a empresarios en 4 decisiones críticas: People, Strategy, Execution, Cash.

**Stack:** Python ≥3.10, SQLite (WAL mode), `http.server` vanilla. Cero dependencias externas declaradas (solo stdlib + pytest para tests).

**Madurez:** Herramienta interna en producción activa. 25 épicas completadas, 510 tests, 249 conceptos en knowledge graph. Madurez media-alta.

**Arquitectura en capas:**

```
HTTP (server.py, router.py, cors.py)
  └─ Handlers (handlers.py: Companies, Worksheets, Sessions, Memory)
      └─ DAOs (daos/: CompanyDAO, WorksheetDAO, SessionDAO, ChangeDAO)
          └─ SQLite (escala_server/schema.py: 7 tablas, 11 índices)

Motor de Conocimiento (independiente de HTTP):
  graph_engine.py        → Grafo entidad-relación en SQLite
  memory_engine.py       → Facts con trust scoring
  knowledge_handler.py   → Búsqueda semántica sobre YAML
  verne_handler.py       → Respuestas "estilo Verne" con templates

Coaching (CLI + engine):
  coaching/ → router, diagnose, worksheet, dashboard, export, pulse, welcome, level, progress
  coaching/class_intake.py, pattern_extraction.py, skill_deltas.py, class_report.py

Conocimiento Declarativo:
  conocimiento/ → 80+ YAMLs: conceptos, métricas, tools, worksheets por decisión

Escala Skills:
  escala-skills/ → 42 sub-skills Markdown para comandos /escala-*
```

**Directorios clave:**
| Directorio | LOC aprox | Descripción |
|---|---|---|
| `escala_server/` | ~2,800 | Core: HTTP, handlers, DAOs, grafo, Verne, migración |
| `coaching/` | ~1,400 | Motor de coaching: diagnose, worksheet, dashboard, export |
| `conocimiento/` | ~80 YAMLs | Base de conocimiento declarativa |
| `tests/` | ~4,580 | 22 archivos, 510 tests |
| `escala-skills/` | ~42 MDs | Skills para comandos CLI |
| `work/epics/` | 26 dirs | Documentación de épicas (con duplicados E18-E22) |

---

## 2. Informe de Auditoría

### 🔴 CRÍTICOS

**A1. Migración rota — columnas inexistentes en SQLite**
- `escala_server/migrate.py:441-442` — Inserta `(id, data_json)` en `companies`. Schema real (`schema.py:24-31`): columnas `(id, name, industry, metadata)`. No existe `data_json`.
- `escala_server/migrate.py:461,480,499` — Mismo bug en `worksheets`: usa `data_json`, schema tiene `data`.
- **Consecuencia:** `sqlite3.OperationalError` en runtime. Código nunca ejecutado contra schema real.
- **Severidad:** CRÍTICA

**A2. Sin manejo de errores en handlers HTTP**
- `escala_server/server.py:29-68` — `do_GET`, `do_POST`, `do_PATCH` sin try/except. Handler que lanza → worker crashea.
- `json.loads` en línea 57 con body malformado → excepción no capturada → thread muerto.
- **Consecuencia:** Servidor requiere reinicio manual tras error de parseo. Sin supervisor de procesos.
- **Severidad:** CRÍTICA

**A3. Parser YAML casero de 340 líneas sin tests**
- `escala_server/migrate.py:22-355` — Implementación propia porque "PyYAML is not available".
- 0 tests. Maneja subset de YAML (comentarios, anidamiento, listas, block scalars, comillas, booleanos, nulls, enteros, floats).
- **Consecuencia:** Edge cases no cubiertos. Datos migrados incorrectamente sin error visible.
- **Severidad:** CRÍTICA

### 🟠 ALTOS

**A4. CORS completamente abierto**
- `escala_server/cors.py:10` — `Access-Control-Allow-Origin: *`
- **Consecuencia:** Si servidor se expone en red (el CLI acepta `--host`), cualquier origen puede leer datos.
- **Severidad:** ALTA

**A5. Serialización JSON manual frágil**
- `escala_server/cash/generate_dashboards.py:498` — `str(db["metrics"]).replace("'", '"').replace('"key"', "'key'")...`
- **Consecuencia:** JavaScript malformado si valores contienen comillas. Sin tests de output HTML.
- **Severidad:** ALTA

**A6. Directorios de épicas duplicados (E18-E22)**
- 10 directorios para 5 épicas. Graph builder detecta y skipea, pero ambigüedad persiste.
- **Consecuencia:** Confusión sobre scope canónico. Riesgo de trabajar en épica equivocada.
- **Severidad:** ALTA

### 🟡 MEDIOS

**A7. Sin CI/CD ni pre-commit hooks** — 510 tests solo se ejecutan manualmente.
**A8. Sin dependencias declaradas** — `pyproject.toml` vacío. `pip install .` no instala nada.
**A9. verne_handler.py monolítico (499 LOC)** — Templates hardcodeados que deberían ser YAML.
**A10. Duplicación ligera** — `_strip_quotes` y `_parse_scalar` repiten lógica de quotes.

### 🟢 FORTALEZAS

1. **510 tests con aserciones concretas** — validan números exactos (42 entidades, 59 relaciones, 3 cambios)
2. **Patrón DAO limpio** — `BaseDAO` con conexión compartida + context manager transaccional
3. **Type annotations consistentes** — `from __future__ import annotations` + dataclasses
4. **Operaciones idempotentes** — `INSERT OR IGNORE`, `ON CONFLICT`
5. **Graph engine con entity resolution** — `resolve_entities()` para deduplicación semántica
6. **80+ YAMLs declarativos** — separación limpia entre código y conocimiento
7. **Arquitectura en capas sin dependencias circulares**
8. **Router HTTP limpio** — 56 líneas, regex con path params

---

## 3. Estrategia de Mejora

### Tema 1: Infraestructura de Calidad Invisible
**Objetivo:** CI en cada push, deps declaradas, cobertura ≥80%.
**Principio:** La calidad que no está automatizada no existe.
**No hacemos:** Dockerizar, staging environments, FastAPI.

### Tema 2: Código No Ejercitado = Código Roto
**Objetivo:** Eliminar parser YAML casero, arreglar/eliminar migrate.py, consolidar épicas.
**Principio:** Código sin tests Y sin ejecución real es basura.
**No hacemos:** Tests para migrate.py si la migración ya ocurrió (eliminar en vez de testear).

### Tema 3: Resiliencia Runtime
**Objetivo:** Handlers HTTP no crashean. CORS restrictivo por defecto.
**Principio:** Un servidor que se cae con JSON malformado es un prototipo con suerte.
**No hacemos:** Migrar a FastAPI, agregar autenticación, PostgreSQL.

### Tema 4: Deuda de Simplicidad
**Objetivo:** Templates Verne a YAML. json.dumps() en dashboards. pyyaml como dependencia.
**Principio:** El proyecto ya tomó las decisiones correctas — terminar de aplicarlas.
**No hacemos:** Refactorizar session_close.py (406 LOC, complejidad inherente al dominio).

---

## 4. Plan de Tareas

### Quick Wins (hacer inmediatamente, <1h cada uno)

| ID | Tarea | Archivos |
|----|-------|----------|
| QW1 | `pyproject.toml` + `pyyaml`, eliminar parser YAML casero | `pyproject.toml`, `migrate.py` |
| QW2 | `json.dumps()` en `generate_dashboards.py` | `generate_dashboards.py:498` |
| QW3 | `try/except` en handlers HTTP | `server.py:29-68` |

### Hito 0 — Red de Seguridad (S, <3h total)

| ID | Tarea | Criterio de aceptación |
|----|-------|----------------------|
| T0.1 | GitHub Actions CI (pytest + ruff) | PR merge bloqueado si CI falla |
| T0.2 | Dependencias en `pyproject.toml` | `pip install -e ".[dev]" && pytest` funciona |

### Hito 1 — Arreglos Críticos (S, <3h total)

| ID | Tarea | Criterio |
|----|-------|----------|
| T1.1 | Arreglar/eliminar migrate.py | `migrate_from_yaml(":memory:", ...)` no lanza excepción |
| T1.2 | Error handling HTTP (400/500) | POST con `{invalid` → 400, no crash |
| T1.3 | CORS restrictivo (localhost default) | `Origin: evil.com` → sin CORS allow |

### Hito 2 — Alto Impacto (M, ~5h total)

| ID | Tarea | Criterio |
|----|-------|----------|
| T2.1 | Extraer templates Verne a YAML | `verne_handler.py` < 350 LOC, tests pasan |
| T2.2 | Consolidar épicas duplicadas E18-E22 | 1 directorio por epic, graph sin warnings |
| T2.3 | pytest-cov en CI | CI reporta cobertura % |

### Hito 3 — Pulido (S, <1h total)

| ID | Tarea | Criterio |
|----|-------|----------|
| T3.1 | Eliminar `_strip_quotes` duplicado | Una sola función maneja quotes |
| T3.2 | `.gitattributes` para YAML/Python | `git add --renormalize .` sin cambios spurios |

**Esfuerzo total:** ~12 horas (2 días). 13 tareas. 12 small, 1 medium.

### Esbozos de Implementación

**T1.1 (migrate.py):**
1. Leer `schema.py` para confirmar nombres de columna reales
2. Reemplazar `data_json` → `data` en queries de worksheets
3. Companies: corregir INSERT a `(id, name, metadata)` extrayendo nombre del profile
4. Test con `:memory:` y directorio temporal con `profile.md` mínimo
5. Verificar `status: "ok"` y `errors: 0`

**T1.2 (error handling HTTP):**
1. Extraer lógica común de `do_POST`/`do_PATCH` a `_handle_api_request(method, path)`
2. Envolver: `json.JSONDecodeError` → 400, `Exception` → 500
3. No modificar `do_GET` (solo dispatch, sin parseo de body)
4. Test: iniciar server en puerto aleatorio, POST con body inválido, verificar 400
5. Trampa: `http.server` usa threads — el test verifica respuesta HTTP, no sobrevivencia de thread

**T2.1 (templates a YAML):**
1. Crear `conocimiento/coaching/verne-templates.yaml`
2. `VerneHandler.__init__` carga con `yaml.safe_load()`
3. Reemplazar `_VERNE_TEMPLATES[category]` por `self._templates[category]`
4. Tests existentes deben pasar sin cambios
5. Trampa: `_DAILY_CHECKLIST` tiene schema diferente — mantener separado o unificar

---

## 5. Preguntas Abiertas

1. **¿ migrate.py ya cumplió su propósito?** Si la migración `.scaleup/` → SQLite fue one-shot, eliminar es más seguro que arreglar. ¿Se re-ejecuta?

2. **¿Cuál de cada par de épicas duplicadas es canónica?** E18: `class-to-skill-learning-loop` (tiene retrospectiva en main) vs `escala-server`. ¿La segunda es parte de E18 o independiente?

3. **¿El servidor se expone a red?** Si solo es localhost, CORS `*` es irrelevante y T1.3 baja a prioridad baja. Si se expone en HostiMoon (2.24.67.207), urgente.

4. **¿Se planean nuevas categorías en VerneHandler?** Si sí, T2.1 es urgente. Si no, puede esperar.
