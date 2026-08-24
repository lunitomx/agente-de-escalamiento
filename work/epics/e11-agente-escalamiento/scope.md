# Epic Scope: E11 — Agente de Escalamiento (repo público)

**Status:** Complete
**Audited:** 2026-08-24

## Objective

Crear un repositorio público `agente-de-escalamiento` en GitHub que contenga los skills de escalamiento de negocios (categoría scaleup-*) completamente anonimizados, con atribución explícita a los autores originales de las metodologías en las que se inspira, y listo para ser instalado por estudiantes de licenciatura en Hermes Agent, Codex CLI y Claude Code.

## Value

- Los estudiantes pueden instalar el agente sin acceso al repositorio interno de desarrollo
- Se respetan los derechos de autor mediante atribución explícita
- El agente es instalable en las 3 plataformas principales de IA
- El código fuente es público y verificable

## In Scope (MUST)

1. Crear repo público `agente-de-escalamiento` en GitHub (cuenta personal de Eduardo)
2. Migrar y anonimizar profundamente todos los skills de la categoría scaleup-*
3. Implementar sistema de atribución — cada metodología referencia a su autor original
4. Configurar instalabilidad en Hermes Agent, Codex CLI y Claude Code
5. README completo con instrucciones de instalación y uso
6. Push del código y verificación final

## In Scope (SHOULD)

- Sección de referencias y atribuciones en el README

## Out of Scope

- Skills de Kokoro, RaiSE u otras categorías no relacionadas con escalamiento
- Datos de clientes reales o información de negocio
- Nuevas funcionalidades no presentes en los skills originales
- Traducción del agente a otros idiomas

## Done Criteria

- [x] Repo `agente-de-escalamiento` creado y público en GitHub
- [x] Todos los skills scaleup-* migrados y anonimizados
- [x] Cada mención a metodología incluye atribución al autor original
- [x] README documenta instalación en Hermes, Codex CLI y Claude Code
- [x] Instalación desde clon fresco verificada en el cierre
- [x] Repositorio verificado sin referencias al proyecto interno ScaliingUPAI

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Quedar referencias internas sin anonimizar | Alta | Media | Revisión manual de cada archivo migrado |
| Atribución incorrecta o insuficiente | Media | Alta | Verificar cada referencia contra fuentes originales |
| Instalación falla en alguna plataforma por paths absolutos | Media | Alta | Usar paths relativos para skills |

## Stories

### S11.1: Crear repo público y estructura base (XS)
Crear el repositorio `agente-de-escalamiento` en GitHub, vacío. Configurar README inicial, LICENSE (MIT), .gitignore y estructura de directorios para skills.

**Depends on:** nada

### S11.2: Anonimización profunda de skills scaleup-* (XL)
Migrar todos los skills de la categoría scaleup-* del repositorio interno al nuevo repo. Anonimizar:
- Renombrar "Scaling Up" → "Escalamiento de Negocios" (o equivalente genérico)
- Renombrar "Rockefeller Habits" → "Hábitos de Ejecución"
- Renombrar "Verne Harnish" → referencias indirectas + atribución
- Renombrar nombres de skills (scaleup-* → escala-*)
- Eliminar referencias a paths absolutos del repo interno
- Reescribir ejemplos para que sean genéricos
- Revisar cada skill línea por línea para eliminar marcas registradas

**Depends on:** S11.1

### S11.3: Sistema de atribución (S)
Agregar en cada skill que mencione una metodología una referencia clara al autor original. Crear archivo de atribuciones (`ATTRIBUTIONS.md`) en la raíz del repo con:
- Lista de metodologías y sus autores
- Descripción de cómo se usan (inspiración, adaptación)
- URLs a fuentes originales donde sea posible
- Nota legal de uso educativo

**Depends on:** S11.2

### S11.4: Instalabilidad multiplataforma (M)
Configurar el repo para que se pueda instalar en:
- **Claude Code:** SKILL.md + scripts de instalación en ~/.claude/skills/escala-*/
- **Hermes Agent:** skills en ~/.hermes/skills/escala-*/
- **Codex CLI:** skills en formato compatible
Crear script `install.sh` que automatice la instalación detectando la plataforma.

**Depends on:** S11.2

### S11.5: Documentación para estudiantes (S)
README completo con:
- ¿Qué es el Agente de Escalamiento?
- Requisitos (tener Claude Code / Hermes / Codex instalado)
- Instalación paso a paso
- Comandos disponibles
- Ejemplo de uso
- Atribuciones y referencias
- FAQ

**Depends on:** S11.4

### S11.6: Push y verificación final (XS)
Push de todo el código al repo público. Verificar:
- Clonar en directorio temporal
- Seguir README para instalar
- Probar al menos 2 skills
- Confirmar que no hay referencias internas filtradas
- Cerrar épica con retrospectiva

**Depends on:** S11.5

## Implementation Plan

### Sequencing Strategy: Quick Win + Dependency-Driven

Este épico es secuencial por naturaleza — cada historia produce un artefacto que la siguiente necesita. Por eso se usa una combinación de Quick Win (S11.1: crear repo es inmediato y da momentum) seguido de Dependency-Driven para el resto.

| Posición | Story | Tamaño | Depende de | ¿Por qué aquí? |
|----------|-------|:------:|:----------:|----------------|
| 1 | S11.1: Crear repo y estructura | XS | — | Quick win — sin repo no hay nada. Da estructura base para el resto |
| 2 | S11.2: Anonimización profunda | XL | S11.1 | El corazón del épico. Depende de tener directorio donde escribir |
| 3 | S11.3: Sistema de atribución | S | S11.2 | Necesita saber qué skills existen y qué conceptos referencian |
| 4 | S11.4: Instalabilidad multiplataforma | M | S11.2 | Skills deben existir antes de crear instalador |
| 5 | S11.5: Documentación | S | S11.4 | README explica cómo instalar — necesita que instalador exista |
| 6 | S11.6: Push y verificación | XS | S11.5 | Todo debe estar listo antes de push público |

### Critical Path

```
S11.1 → S11.2 → S11.3 → S11.4 → S11.5 → S11.6
```

100% lineal. No hay oportunidades de paralelización porque cada historia produce un artefacto que la siguiente consume.

### Milestones

| Milestone | Stories | Criterio de éxito |
|-----------|---------|-------------------|
| **M1: Base lista** | S11.1 | Repo creado con estructura de directorios. Primer commit con README inicial y LICENSE |
| **M2: Skills anonimizados** | S11.2, S11.3 | Los 39 skills migrados, renombrados, sin referencias a marcas registradas. ATTRIBUTIONS.md creado |
| **M3: Instalable y documentado** | S11.4, S11.5 | `install.sh` funciona en las 3 plataformas. README completo con instrucciones |
| **M4: Épico completo** | S11.6 | Push a GitHub, verificación desde clon fresco, retrospectiva |

## Progress Tracking

| Story | Status | Started | Completed | Notes |
|-------|--------|---------|-----------|-------|
| S11.1: Crear repo y estructura | Done | 2026-05-24 | 2026-05-24 | Repo creado, LICENSE corregido, README listo |
| S11.2: Anonimización profunda | Done | 2026-05-24 | 2026-05-24 | 39 skills migrados y anonimizados |
| S11.3: Sistema de atribución | Done | 2026-05-24 | 2026-05-24 | ATTRIBUTIONS.md + 17 skills atribuidos |
| S11.4: Instalabilidad multiplataforma | Done | 2026-05-24 | 2026-05-24 | install.sh creado |
| S11.5: Documentación | Done | 2026-05-24 | 2026-05-24 | README completo con FAQ |
| S11.6: Push y verificación | Done | 2026-05-24 | 2026-05-24 | Verificado desde clon fresco |

### Sequencing Risks

| Risk | Mitigation |
|------|-----------|
| S11.2 (XL) es la historia más grande y la más propensa a errores | Dividir en batches de 10 skills para revisión incremental |
| S11.4 puede fallar si Codex CLI no tiene ruta de instalación documentada | Priorizar Hermes + Claude, Codex como bonus |
| El push a GitHub requiere token de acceso configurado | Eduardo debe tener token listo antes de S11.6 |
