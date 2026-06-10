# Auditoría integral — Agente de Escalamiento (ScaleUp / Escala)

**Fecha:** 2026-06-02
**Auditor:** sesión RaiSE (full-stack + QA)
**Alcance:** entendimiento del sistema · calidad de últimas 10 épicas (E16–E25) · verificación de los 4 issues de GitHub contra HEAD · salud QA · consistencia de la migración ScaleUp→Escala
**Método:** lectura de código + reproducción ejecutable (no se confió en la descripción de los issues) + 5 agentes de auditoría en paralelo.

---

## 0. Qué es el producto

Coach de IA **local-first** que implementa la metodología *Scaling Up* (Verne Harnish) dentro de Claude Code (y portado a Hermes/Codex). El usuario clona el repo, abre Claude Code, y obtiene un coach que lo guía por las 4 decisiones (People, Strategy, Execution, Cash) con memoria persistente, 34 worksheets, diagnóstico con scoring 1–5 y dashboards visuales.

**Arquitectura real (verificada en código):**
- **Núcleo Python** `coaching/` — módulos por dominio (`welcome`, `diagnose`, `worksheet`, `progress`, `level`, `router`, `pulse`, `export`, `summary`, `dashboard`). Patrón `run(context: dict) → {output, artifacts, errors}`.
- **Servidor HTTP opcional** `escala_server/` — `http.server` stdlib + SQLite (`~/.escala/escala.db`), handlers/DAOs, changelog a nivel de campo, retrieval sobre la ontología, clasificador semántico "Verne".
- **Capa de skills** — adapters `SKILL.md` que orquestan bash + Python. **Existen 3 sets:** `escala-skills/escala-*` (canónico según `install.sh`), `.claude/skills/scaleup-*` (viejo, aún commiteado), `escala-agent/skills/` (variante aparte).
- **Ontología** `conocimiento/*.yaml` (duplicada en `.scaleup/knowledge/`).
- **Datos de usuario** bajo `.scaleup/` (prefijo canónico del código) — pero los skills `escala-*` documentan `.escala/`.

**Para quién:** emprendedores / empresas en escalamiento (mercado Scaling Up, ~20k empresas globalmente).

---

## 1. Diagnóstico raíz: migración ScaleUp → Escala incompleta

Los 4 issues no son bugs aislados: son **síntomas de un rename a medio camino**. Evidencia: dos sets de skills en paralelo, dos remotes (`scaleupagent` en GitLab, `agente-de-escalamiento` en GitHub), prefijos `.scaleup`/`.escala` mezclados, refs `knowledge/*.md` vs `conocimiento/*.yaml`, y el commit reciente "corrección URLs del repo".

Conteos: `.scaleup` = 187 matches / 81 archivos · `.escala` = 170 matches / 56 archivos.

**Contradicción de canonicidad:** `install.sh` instala desde `escala-skills/` (canónico = *escala*), pero `CLAUDE.md` (el system prompt activo) documenta `.claude/skills/scaleup-*` y rutas `.scaleup/coaching/`. Los dos documentos rectores se contradicen.

---

## 2. Verificación de los 4 issues (contra HEAD, reproducido)

| Issue | Veredicto | Qué sigue vivo |
|---|---|---|
| **#1** company_name vs name bloquea onboarding | **YA-ARREGLADO** (headline) + **DERIVÓ** (path) | `run()` acepta `company_name` y crea perfil OK (repro exit 0). El `REQUIRED_FIELDS=["name"]` vive en `coaching/welcome/engine.py` que es **código muerto huérfano** (0 imports). Lo vivo: split de path — escribe `.scaleup/agent/memory/company-profile.yaml` pero el validator escala revisa `.escala/...`. |
| **#2** 8 refs knowledge `.md` vs `.yaml` | **VIVO (8/8 + más)** | Las 8 (en realidad 15) referencias `knowledge/...md` no existen; el real es `conocimiento/...yaml` con nombre corto. Persiste post-install. Fix mecánico. |
| **#3** 4 sub-agents + 3 overviews faltantes | **PARCIAL (mal contado)** | Sub-agents: **4/4 EXISTEN** en `.scaleup/agent/sub-agents/`. Overviews: faltan **4** (incl. cash), no 3 — cero existen en el repo. |
| **#4** worksheet save ignora base_path + sobrescribe | **PARCIAL → headline DERIVÓ** | `save`, `get_completed_ids` y los loads **SÍ honran `base_path`** (repro 2 negocios: aislamiento total, sin clobber cruzado). Lo único vivo: **overwrite silencioso sin respaldo ni confirmación** dentro del mismo `base_path` (`coaching/worksheet/__init__.py:295`). |

### El matiz crítico del #4 (el que te preocupa)
El propio issue lo aclara y la reproducción lo confirma: **el engine NO causó tu pérdida real de datos.** La carpeta `worksheets/` está vacía (nada se guarda aún por esa vía) y el aislamiento por `base_path` funciona. Tu pérdida vino de **plantillas de mega-prompts con nombres fijos** (`mi-estrategia-en-una-frase.html`, `core-customer.html`, …) que guardan sin el nombre del negocio — y **viven fuera de este repo**, en el curso. Son dos arreglos distintos:
- **En este repo:** endurecer `save` contra overwrite silencioso (preventivo/latente).
- **Fuera de este repo (curso/plantillas):** corregir la convención de nombres fijos — esto es lo que de verdad te dolió y debe tratarse por separado.

---

## 3. Hallazgos estructurales más allá de los 4 issues

| # | Severidad | Hallazgo | Evidencia |
|---|---|---|---|
| H1 | **P0** | Engine emite comandos `/scaleup-*` en **45 lugares**, pero el set canónico es `escala-*` → el coach le dice al usuario que ejecute comandos del set viejo/stale | `coaching/core/__init__.py:66-70`, `coaching/export/__init__.py:34-37`, `coaching/pulse/__init__.py:64` |
| H2 | **P0** | 26 SKILL.md `escala-*` referencian un árbol `.escala/` repo-local que **no existe**; el engine escribe `.scaleup/` | `escala-welcome/SKILL.md:22,55,71` vs `coaching/welcome/__init__.py:23` |
| H3 | **P0** | 15 referencias `knowledge/...md` rotas en ambos sets (issue #2 ampliado) | tabla en §2 |
| H4 | **P0** | 4 `overview.md` por decisión faltantes (issue #3) | `escala-{people,strategy,execution,cash}/SKILL.md:24` |
| H5 | **P1** | Bug SQLite latente: `init_db` hace `connect()` sin `uri=True` | `escala_server/daos/schema.py:53`; fix = reapuntar import en `daos/__init__.py:13` a `..schema` (la versión correcta ya existe) |
| H6 | **P1** | 2 tests fallando: parser YAML casero no parsea listas | `tests/test_escala_migration.py:48,93` (`_parse_simple_yaml`) |
| H7 | **P1** | 3 árboles Python/knowledge duplicados (drift silencioso) | `validators/` ≡ `.scaleup/agent/validators/`; `conocimiento/` ≡ `.scaleup/knowledge/`; `.scaleup/coaching/` es cascarón vacío |
| H8 | **P1** | `CLAUDE.md` contradice `install.sh` sobre el set canónico | `CLAUDE.md:76-81` vs `install.sh:75` |
| H9 | **P1** | Find-replace corrupto anida "(OPSP)" recursivamente | `escala-strategy-opsp/SKILL.md:2` |
| H10 | **P2** | `pytest` pelado no colecta (muere en `referencias-humberto/`); falta `[tool.pytest.ini_options]` | `pyproject.toml` |
| H11 | **P2** | 7 `.pyc` trackeados pese a `.gitignore`; 49 archivos basura SQLite (`:memory:`, `file:test_*`) en root | `git ls-files | grep .pyc` |
| H12 | **P2** | README clona `scaleupagent` (nombre viejo) vs scripts usan `agente-de-escalamiento` | `README.md:11-12` |
| H13 | **P2** | `except Exception: pass` traga errores de YAML | `coaching/core/__init__.py:39` |
| H14 | **P2** | Código muerto: `coaching/welcome/engine.py` (huérfano); `__main__.py` importa `_main` inexistente | — |

---

## 4. Auditoría de las 10 épicas (E16–E25)

**Veredicto general: ejecución sólida, governance débil.** La *programación* de la línea de software (E18a, E19a, E21a, E22a) siguió RaiSE con TDD real, retros honestas y suites verdes (salvo 2 fallas conocidas). La debilidad es de **gobierno**, no de código.

### La colisión de numeración E18–E22
Hay **dos líneas de roadmap que colisionaron** en los números 18–22:
- **Línea A — Software (ejecutada y commiteada, con tags):** `e18-escala-server`, `e19-book-ingestion`, `e20-contextual-skills`, `e21-verne-board-member`, `e22-verne-audit`.
- **Línea B — Curriculum (planeada, NUNCA commiteada, 0 archivos en git):** `e19-strategy-core-skills`, `e20-voice-of-customer`, `e21-transcript-intelligence`, `e22-validation-drift-governance`.

**El caso E18 es el más grave:** son **dos épicas reales y ambas commiteadas**. `e18-escala-server` (12 stories, 193 tests) es dueña del tag `epic/e18-complete`. Pero `e18-class-to-skill-learning-loop` (4 stories, HEAD actual) tiene 22 archivos en git y su propia retro **pero ningún tag** — huérfana bajo un número ya cerrado. **Causa raíz:** `work/` está en `.gitignore`, lo que rompe la trazabilidad y permitió numerar a ciegas.

### Top 5 problemas de governance
1. Colisión E18 entre dos épicas reales (número + tag únicos para dos cuerpos distintos).
2. 4 stubs sin commitear (E19b–E22b) mezclados con épicas reales del mismo número.
3. Cierres no-monótonos/prematuros: E22 cerrada *después* de E23/E24; E25 cerrada con S25.5 pendiente (hecha 1h40 después del tag).
4. E16/E17 completas pero **sin tag de cierre**.
5. Roadmap congelado en E17 (~8 épicas desactualizado) + 2 tests rojos no resueltos.

---

## 5. Backlog de arreglo priorizado

### P0 — rompe funcionalidad (decidir prefijo/canon y converger)
1. **Decidir prefijo único** (`.escala` vs `.scaleup`) y converger engine + skills + docs.
2. **H1** — Reapuntar los 45 routing strings `/scaleup-*` → `/escala-*` en `coaching/`.
3. **#2 / H3** — Reapuntar las 15 refs knowledge a los `.yaml` reales de `conocimiento/`.
4. **#3 / H4** — Crear los 4 `overview.md` (o reapuntar a `conocimiento/decisions/*.yaml`).

### P1 — calidad / corrección
5. **#4** — Endurecer `save` contra overwrite silencioso (respaldo `.bak` o `overwrite: true`).
6. **H5** — Fix bug SQLite (`daos/__init__.py:13` → `from ..schema import init_db`).
7. **H6** — Arreglar los 2 tests (usar PyYAML en vez del parser casero).
8. **H7/H8** — Eliminar árboles duplicados; sincronizar `CLAUDE.md` con `install.sh`.
9. **H9** — Reparar anidamiento OPSP corrupto.

### P2 — higiene / cosmético
10. **H10** — Agregar `[tool.pytest.ini_options]` con `testpaths`/`norecursedirs`.
11. **H11** — `git rm --cached` los 7 `.pyc`; borrar basura SQLite del working tree.
12. **H12** — Unificar nombre de repo en `README.md`.
13. **H13/H14** — Endurecer `read_yaml`; borrar código muerto (`welcome/engine.py`).

### Governance (épicas)
14. Re-secuenciar numeración (renumerar la segunda E18 → E26+); decidir destino de los 4 stubs.
15. Taguear E16/E17; sacar `work/epics/` del `.gitignore` (o índice trackeado).
16. Actualizar `product-roadmap.md` (congelado en E17).

---

## 6. Salud QA (números reales)

- **Suite (scope proyecto):** 466 recolectados · **462 passed · 2 failed · 2 skipped**.
- `pytest` pelado **no colecta** (muere en `referencias-humberto/`).
- `.venv` **no tiene pytest** instalado (solo corre con python3 del sistema).
- **Cobertura faltante:** `coaching/summary`, `coaching/progress`, `coaching/worksheet` (dir de tests vacío), `escala_server/cli.py`.
