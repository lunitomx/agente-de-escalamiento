---
epic_id: "E47"
title: "Coherencia del viaje instalado: Workspace, OPSP y Feedback"
status: "done"
retrospective_date: "2026-08-21"
jira_key: "ESCALA-1"
---

# E47 — Retrospectiva

## Resumen ejecutivo

E47 nació para hacer coherente el recorrido instalado de ESCALA: que Codex operara RaiSE por MCP sin abrir secretos, que el OPSP tuviera estructura real y persistencia local, y que un usuario pudiera reportar bugs o mejoras sin transferir datos de su empresa.

Se entregaron **8 de 9 stories**. Una story (S47.8 — evitar contaminación cross-repo en `rai graph query`) quedó fuera de alcance porque RaiSE es herramienta interna de desarrollo, no dependencia del producto ESCALA. El fix de referencia se dejó documentado para raise-commons.

## Qué se planeó vs. qué pasó

| Story | Plan original | Resultado | Notas |
|---|---|---|---|
| S47.1 | Contrato Workspace Codex/MCP | Done | CLI sandbox falla comprensible; Codex usa MCP; provisionado no ensucia worktree. |
| S47.2 | Instalador, recursos y migración | Done | Nueva y existente instalación reciben skills compatibles sin duplicados. |
| S47.3 | OPSP completo y coherente | Done | Guía representa columnas, filas, responsables y capacidades sin contradicciones. |
| S47.4 | Persistir, reanudar y exportar OPSP | Done | Estado estructurado en `.escala/my-company/opsp.yaml` + export `opsp.md`. |
| S47.5 | Feedback contextual local | Done | Reutilizó `escala-bugreport/SKILL.md`; reporte redactado y confirmado, sin envío automático. |
| S47.6 | Calificación y release | Done | Instalación aislada verificada, regresión 1097 passed (1 fallo preexistente ajeno), canary de privacidad en verde. |
| S47.7 | Sincronizar clones del repo | Done | Fix en `escala-skills/` llega al clon que sirve symlinks activos (`agente-de-escalamiento`). |
| S47.8 | Evitar contaminación cross-repo en `rai graph query` | Fuera de alcance | RaiSE no es dependencia del producto; fix dejado en raise-commons. |
| S47.9 | Company State Document como Project de ChatGPT | Done | Documento de estado subible a ChatGPT Projects con instrucciones equivalentes a Claude. |

## Métricas de éxito

- **Instalación aislada:** verificada, 62 skills, sin duplicados.
- **Regresión:** 1097 passed, 1 fallo preexistente ajeno.
- **Canary de privacidad:** en verde.
- **Jira:** Epic `ESCALA-1` y story `ESCALA-2` creados.
- **Historias completadas:** 8/9 (88.9 %).

## Qué funcionó

1. **Definir el contrato de workspace primero (S47.1).** Desbloqueó el resto de la épica y evitó decisiones de instalación inconsistentes.
2. **Persistencia como estado estructurado + Markdown.** Permite reanudar, validar y leer sin inventar respuestas.
3. **Reutilizar `escala-bugreport` existente** en lugar de crear feedback desde cero.
4. **Auditoría de producto durante la épica** que agregó S47.7-S47.9 y evitó dejar sincronización y multiplataforma para después.
5. **Gates automáticos con evidencia numérica** antes de declarar Done.

## Qué no funcionó / lecciones

1. **Subestimar la sincronización de clones.** S47.7 surgió porque dos copias locales del repo habían divergido silenciosamente; debería ser parte del contrato de instalación, no una corrección tardía.
2. **Asumir que "RaiSE es interno" era suficiente descarte.** S47.8 se movió fuera de alcance, pero la contaminación cross-repo sigue siendo un riesgo para desarrolladores. Necesita dueño en raise-commons.
3. **Mezclar alcance de plataforma (Claude + ChatGPT) durante la épica.** Fue correcto, pero agregó churn; debería haberse declarado en el brief desde el inicio.
4. **El fallo preexistente ajeno en regresión** sigue sin dueño. Cada épica que lo vea debería documentarlo o asignarlo.

## Sorpresas

- Los symlinks activos de los coaches apuntaban a un clon distinto del que se editaba (`agente-de-escalamiento`).
- `rai graph query` sin `--strategy` caía en fallback cross-repo; afecta solo desarrollo, pero es confuso.
- ChatGPT Projects requiere instrucciones equivalentes pero no idénticas a Claude; el mismo Company State Document sirve con adaptaciones menores.

## Deuda técnica y riesgos remanentes

| Ítem | Riesgo | Propuesta |
|---|---|---|
| S47.8 fuera de alcance | Desarrolladores confundidos por contexto cross-repo | Crear issue en raise-commons o incluir en épicar de herramientas internas. |
| Fallo preexistente en regresión | Ruido en gates; posible regresión no detectada | Aislar en bug aparte o marcar como `xfail` con justificación. |
| Dos clones del repo | Seguir divergiendo | Automatizar sincronización o documentar flujo de trabajo único. |
| Permisos MCP/secretos | Escalamiento de permisos en futuras integraciones | Revisar boundary en cada nueva historia que toque `.codex/config.toml` o `.mcp.json`. |

## Items movidos a parking lot

- **S47.8 — Contaminación cross-repo en `rai graph query`:** fuera de alcance de producto ESCALA; candidato para raise-commons o épicar de developer experience.
- **Automatización de sincronización de clones:** la story S47.7 sincronizó una vez; falta hacerlo repetible.
- **ChatGPT Projects como flujo activo:** la subida es manual; una futura story podría automatizar la exportación vía API si hay demanda.

## Recomendaciones para siguientes épicas

1. **Incluir el contrato de instalación y sincronización de clones en el brief desde el inicio.** No esperar a una auditoría para detectarlo.
2. **Definir claramente qué es producto vs. herramienta interna** al decidir alcance de RaiSE/raise-commons.
3. **Mantener un registro de fallos preexistentes** con dueño, para que no se repita en cada retrospectiva.
4. **Revisar permisos MCP antes de cada integración nueva**, no después.

## Estado final

E47 se cierra como **Done**. El recorrido instalado de ESCALA es coherente, recuperable y respetuoso de la privacidad. Los items fuera de alcance quedan en parking lot para siguientes épicas de herramientas internas o developer experience.
