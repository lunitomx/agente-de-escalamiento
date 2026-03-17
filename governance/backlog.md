# Backlog: ScaleUp Agent AI

> **Status**: Active
> **Repo**: https://github.com/lunitomx/scaleupagent

## Epics

| ID | Epic | Status | Scope | Priority |
|----|------|--------|-------|----------|
| E1 | OCR Pipeline — Extraer libro completo a texto/markdown | done | RF-01 | P0 |
| E2 | Knowledge Base — Estructurar contenido por las 4 decisiones | done | RF-02 | P0 |
| E3 | Agent Framework — Estructura instalable para GitHub | active | RF-03, RF-07 | P0 |
| E4 | Validación — Testing end-to-end del flujo completo | draft | RF-04, RF-05, RF-06 | P1 |
| E5 | Distribución — Publicar en GitHub y documentar instalación | draft | RF-07 | P1 |

## E3: Agent Framework — Estructura instalable para GitHub

> Goal: Que un empresario clone el repo, abra Claude Code, y tenga el agente ScaleUp funcionando.

| Story | Description | Size | Status |
|-------|-------------|------|--------|
| S3.1 | CLAUDE.md del producto — Identidad, instrucciones base, routing a skills | M | draft |
| S3.2 | .gitignore + limpieza — Excluir archivos de desarrollo RaiSE, PDF, build artifacts | S | in progress |
| S3.3 | README.md — Instrucciones de instalación, qué es, cómo usar | M | draft |
| S3.4 | Estructura de directorios del usuario — `.scaleup/` con company-profile vacío y defaults | S | draft |
| S3.5 | Skill triggers en CLAUDE.md — Mapear slash commands a skills del producto | S | draft |

## E4: Validación — Testing end-to-end

> Goal: Verificar que cada skill funciona correctamente y el flujo es coherente.

| Story | Description | Size | Status |
|-------|-------------|------|--------|
| S4.1 | Test flujo welcome → diagnose → routing | M | draft |
| S4.2 | Test cada sub-agente (people, strategy, execution, cash) genera artifacts correctos | L | draft |
| S4.3 | Test templates se rellenan correctamente | S | draft |
| S4.4 | Fix bugs encontrados en validación | ? | draft |

## E5: Distribución — Publicar en GitHub

> Goal: Repo público funcional con documentación clara.

| Story | Description | Size | Status |
|-------|-------------|------|--------|
| S5.1 | Push inicial a GitHub con estructura limpia | S | draft |
| S5.2 | LICENSE (MIT o similar) | XS | draft |
| S5.3 | Smoke test: clonar repo fresco y verificar que funciona | M | draft |
