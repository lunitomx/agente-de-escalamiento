---
epic_id: "E47"
title: "Coherencia del viaje instalado: Workspace, OPSP y Feedback"
status: "unresolved/review-required"
closure_disposition: "unresolved/review-required"
created: "2026-08-09"
jira_key: "ESCALA-1"
---

# E47 — Coherencia del viaje instalado: Workspace, OPSP y Feedback

## Hipótesis

Una instalación de ESCALA que usa contratos consistentes para el workspace, el OPSP y el feedback permite que una persona complete y retome su plan sin depender de rutas locales inexistentes, conversaciones efímeras ni permisos globales inseguros.

## Métricas de éxito

- Una sesión Codex usa MCP para RaiSE y explica el fallback CLI sin exponer credenciales.
- Una instalación nueva y una existente encuentran los mismos recursos, con migración segura.
- El OPSP se guarda como estado estructurado y se exporta como Markdown sin inventar respuestas.
- Un reporte de bug o mejora sale local, redactado y confirmado por la persona.

## Tamaño

L — seis historias; se entrega primero el contrato de workspace porque desbloquea el resto.

## No-Gos

- No conceder a Codex escritura global sobre directorios que contienen secretos.
- No enviar reportes ni telemetría automáticamente.
- No convertir conversaciones de empresa en datos de entrenamiento.
- No presentar un OPSP incompleto como plan terminado.

## Rabbit Holes

- Reparar solo la copia de un skill en lugar del origen y el instalador.
- Usar el archivo SQLite local legado como si fuera la base activa de RaiSE.
- Resolver permisos Jira/Confluence dentro de una historia de producto sin evidencia de acceso.
