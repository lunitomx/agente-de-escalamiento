# Epic Scope: E26 — Infraestructura de Calidad

**Status:** Draft
**Dependencies:** Ninguna
**Tamaño:** S (3 stories, ~3h)
**Origen:** Auditoría Fable 5 (2026-06-09) — Temas 1 y 2

## Visión

Automatizar la calidad. 510 tests existen pero solo se ejecutan manualmente. Las dependencias no están declaradas — un clone limpio no sabe qué instalar. La cobertura no se mide. Esta épica pone la red de seguridad que el proyecto merece: CI que falla si los tests fallan, dependencias explícitas, y cobertura visible.

## Stories

| Story | Size | Qué |
|-------|:----:|-----|
| **S26.1 — GitHub Actions CI** | S | Crear `.github/workflows/ci.yml` con jobs `test` (pytest) + `lint` (ruff). Ejecutar en push a main y PRs. PR merge bloqueado si CI falla. |
| **S26.2 — Dependencias en pyproject.toml** | S | Agregar `pyyaml` como dependencia core. Agregar `[project.optional-dependencies]` con `dev`: pytest, ruff, pytest-cov. Verificar: `pip install -e ".[dev]" && pytest` funciona en clone limpio. |
| **S26.3 — Cobertura en CI** | S | Agregar `pytest-cov` con `--cov=escala_server --cov=coaching --cov-report=term`. CI publica coverage %. Sin umbral mínimo aún — solo visibilidad. |

## Done Criteria

- [ ] S26.1: CI corre en cada push/PR. PR bloqueado si tests o lint fallan.
- [ ] S26.2: `pyproject.toml` tiene `dependencies` y `[dev]` extras. `pip install -e ".[dev]"` funciona.
- [ ] S26.3: CI reporta porcentaje de cobertura en output.
