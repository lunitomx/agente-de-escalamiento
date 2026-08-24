# Implementation Plan: E21 — Verne Lens Board Member

**Status:** Ready for approval
**Baseline:** main; suite verde el 2026-08-24

## Secuencia

| Orden | Story | Tamaño | Depende de | Hito |
|:---:|---|:---:|---|---|
| 1 | S21.1 — Perfil y contrato | M | E19 schema | M1 |
| 2 | S21.2 — Contexto y recuperación | L | S21.1, E18, E19 | M1 |
| 3 | S21.3 — Daily/consulta | L | S21.2 | M2 |
| 4 | S21.4 — Sesión/distribución | M | S21.3, E10 | M2 |
| 5 | S21.5 — Evaluación/cierre | M | S21.1–S21.4 | M3 |

S21.1–S21.3 son secuenciales. En S21.4 sesión y plataforma pueden separarse si
tienen propietarios de archivos distintos.

## Hitos

| Hito | Incluye | Salida |
|---|---|---|
| M1 — Grounded core | S21.1–S21.2 | `EvidencePacket` válido sin modelo |
| M2 — Walking product | S21.3–S21.4 | Dos modos y E18 compatible |
| M3 — Release candidate | S21.5 | Matriz verde, smoke e inventario |

## TDD por historia

1. Contrato/fixture que falla.
2. Implementación mínima.
3. Errores y adversariales.
4. Suites enfocadas y completa.
5. Evidencia en retrospectiva.
6. Commit verde por story.

## Gates

### Gate 0 — Product approval

- [ ] Nombre/disclosure.
- [ ] Start/close opt-in.
- [ ] Máximo de recomendaciones.

### Gate 1 — Grounding

- [ ] Perfil y contratos versionados.
- [ ] Referencias E19 resolubles.
- [ ] Sin evidence degrada seguro.

### Gate 2 — Product

- [ ] Ambos modos comparten `BoardResponse v1`.
- [ ] Entrada maliciosa permanece dato.
- [ ] E18 funciona sin E21 y tolera fallos.
- [ ] Skill instalado/descubierto en ambas plataformas.

### Gate 3 — Close

- [ ] Casos dorados/adversariales y suite verdes.
- [ ] Smoke real registrado.
- [ ] Retrospectiva e inventario actualizados.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Respuesta no fundamentada | Referencias + validador; fallar cerrado |
| Suplantación | Disclosure y reglas estructurales |
| Provenance de aristas perdida | Citar entidades, no aristas SQLite |
| Clasificación imprecisa | Override y limitación visible |
| Prompt injection | Delimitación y tests adversariales |
| Regresión start/close | Opt-in, fallback y tests feature-off |
| Conteo rígido de skills E10 | Actualizar manifiestos/tests |
| Evaluación subjetiva | Medir contrato; smoke separado |

## Commits

Un commit verde por story. Sin tag hasta Gate 3. Este documento no autoriza
implementar.
