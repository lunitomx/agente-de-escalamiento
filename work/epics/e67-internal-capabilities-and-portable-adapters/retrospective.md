---
epic_id: E67
status: complete
closed: 2026-09-30
---

# E67 — Capacidades internas y adaptadores portables — Retrospective

## Resultado

Las seis historias están mergeadas en `main` y cada una tiene su retro:

| Historia | Entrega | Merge |
|---|---|---|
| S67.1 Capability map | Catálogo MVP; evidencia solo `confirmed` y recibo `receipt.sha256.<hex>` | `4732b77` |
| S67.2 Codex adapter | Una puerta (`escala`); el catálogo se fija contra la autoridad por bytes + id | `01b2dc9` |
| S67.3 Claude adapter | Bloque gestionado en `CLAUDE.md`; marcadores fail-closed | merged |
| S67.4 Paridad/migración | Matriz regenerable de 6 rutas; aliases fuera de las raíces descubribles | merged |
| S67.5 Especialistas | 4 perfiles × 2 plataformas desde el contrato E45; check sin drift | merged |
| S67.6 Agent Plugins v1 | Paquete portable sin MCP, credenciales ni memoria | merged |

Criterios de terminación: técnicamente cumplidos. E68 recibe los builds
instalables y la matriz de paridad S67.4. La **equivalencia semántica entre
modelos** y la **aceptación empresarial** siguen sin declararse aquí:
pertenecen a E68 y al piloto E45.

Gate en `main` (a37b1dd, árbol limpio): 1594 passed, 2 skipped, pyright 0,
ruff limpio.

## Límites honestos al cierre

- La nota "remediation-pending-rereview" de S67.1 quedó cubierta con el fix
  `94114ce` y sus tests de regresión (`tests/test_capability_map.py`); no hubo
  una segunda revisión independiente documentada.
- La autoridad que emite recibos confirmados es E52/E55; E67 solo valida la
  forma del recibo.
- En checkouts con restos locales ignorados (`.agents/skills/scale…up-*`, del
  2026-05-28), 5 tests de S67.4 fallan con
  `legacy_alias_publicly_discoverable`. El validador tiene razón: quitar esos
  restos locales resuelve el fallo; no es un defecto del código.

## Patrones del epic

1. **La autoridad se fija, no se infiere.** Catálogo por bytes + id (S67.2,
   S67.6) y wrappers comparados byte a byte (S67.4). Un artefacto válido según
   el schema no equivale a autorizado.
2. **Superficie = archivos + directorios + raíces descubribles.** Validar solo
   archivos dejó huecos: un directorio vacío (S67.6) y aliases en
   `.agents/skills` (S67.4).
3. **Revisión adversarial independiente paga.** Detectó P1 en S67.1, S67.3,
   S67.4 y S67.6, todos antes del merge.
4. **Cambiar la autoridad exige re-pinear la prueba que la ancla.** S67.3 y
   S67.5 ampliaron `public-export.yaml` sin re-pinear el ledger maestro; se
   pagó en `c079dcd` durante la integración.

## Qué mejorar

- Escribir la retro de cada historia al hacer el merge: S67.2 quedó sin retro
  un mes y bloqueó el cierre.
- Mantener `status` de story.md sincronizado con el merge: S67.2 y S67.6
  seguían en open/in_progress.
- Los tests que escanean las raíces reales del repo dependen de archivos
  ignorados locales. Hay que aislarlos con `tmp_path` o documentar la limpieza
  previa.
