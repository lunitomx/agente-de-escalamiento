---
type: guardrails
version: "1.0.0"
---

# Guardrails: ESCALA Agent AI

---

## Guardrails Activos

### Code Quality

| ID | Level | Guardrail | Verification | Derived from |
|----|-------|-----------|--------------|--------------|
| must-code-lint-001 | must | Todo código Python debe pasar linting con ruff | `ruff check .` sin errores | RF-03 |
| must-code-types-002 | must | Type hints en todas las funciones públicas | `mypy --strict` en módulos core | RF-03 |
| must-code-format-003 | must | Formateo consistente con ruff format | `ruff format --check .` sin cambios | RF-03 |

### Testing

| ID | Level | Guardrail | Verification | Derived from |
|----|-------|-----------|--------------|--------------|
| must-test-unit-001 | must | Cobertura mínima de 80% en módulos core | `pytest --cov` >= 80% | RF-03, RF-04 |
| must-test-ocr-002 | must | Tests de integración para pipeline OCR con sample pages | `pytest tests/integration/ocr/` pasa | RF-01 |
| should-test-skills-003 | should | Cada skill del framework debe tener test de smoke | `pytest tests/skills/` pasa | RF-03 |

### Security

| ID | Level | Guardrail | Verification | Derived from |
|----|-------|-----------|--------------|--------------|
| must-sec-nosecrets-001 | must | No secrets hardcodeados en el código | `gitleaks detect` sin findings | RF-07 |
| must-sec-input-002 | must | Sanitizar toda entrada del usuario antes de procesarla | Code review + tests de injection | RF-04, RF-06 |
| should-sec-deps-003 | should | Dependencias sin vulnerabilidades conocidas | `pip-audit` sin critical/high | RF-07 |

### Content & IP

| ID | Level | Guardrail | Verification | Derived from |
|----|-------|-----------|--------------|--------------|
| must-content-nofull-001 | must | No incluir texto literal completo del libro en el repo distribuible | Review de assets antes de release | RF-02 |
| must-content-transform-002 | must | El conocimiento debe estar transformado en prompts/skills, no como copia textual | Review de estructura de conocimiento | RF-02, RF-03 |
| must-content-public-boundary-003 | must | Todo contenido candidato público debe ser source-neutral, excluir procedencia privada y pasar la política deny-first | `governance/public-boundary.yaml` + `rai gate check gate-tests --scope tests/test_public_boundary.py` | RF-02, RF-03, RF-07 |

### Architecture

| ID | Level | Guardrail | Verification | Derived from |
|----|-------|-----------|--------------|--------------|
| must-arch-modular-001 | must | Arquitectura modular: OCR pipeline, knowledge base y framework como módulos independientes | Estructura de directorios verificable | RF-01, RF-02, RF-03 |
| must-arch-offline-002 | must | El framework instalado debe funcionar sin conexión a servicios externos | Test de ejecución offline | RF-03, RF-07 |
