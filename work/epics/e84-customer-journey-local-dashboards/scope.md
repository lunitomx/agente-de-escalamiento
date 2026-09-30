---
epic_id: E84
title: Customer journey proactivo y tableros analíticos locales
status: planned
jira_key: "ESCALA-50"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E75, E80, E83]
---

# Scope E84

## Objetivo

1. ESCALA pregunta por el **customer journey** del cliente del empresario cuando detecta que hace falta (p.ej. al diagnosticar ventas, marketing o retención), sin esperar a que se lo pidan.
2. ESCALA **sugiere tableros visuales** como lo haría un experto en business analytics: qué medir, por qué y cómo verlo, y los genera **localmente**.

## Dentro

- Disparadores explícitos y probados de cuándo preguntar por el journey (y cuándo no).
- Modelo del journey por etapas con evidencia y huecos declarados.
- Recomendación de tablero: métricas, fuente de cada dato, frecuencia.
- Tableros como archivos locales en la carpeta de la empresa (p.ej. HTML autocontenido), sin publicar en la nube.

## Fuera

- Publicar tableros en servicios externos o enviarlos a terceros.
- Inventar cifras para llenar un tablero; un dato faltante se muestra como faltante.
- Reemplazar el módulo `coaching/dashboard` sin revisar primero qué entrega hoy.

## Incógnitas

1. Qué muestra hoy `coaching/dashboard` y si se extiende o se reemplaza.
2. Formato local que funcione igual desde Claude, Codex y ChatGPT.

## Historias (borrador)

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S84.1 | Disparadores y entrevista del customer journey | M | planned |
| S84.2 | Modelo de journey con evidencia y huecos | M | planned |
| S84.3 | Recomendador de tablero (qué medir y por qué) | M | planned |
| S84.4 | Generador de tablero local | M | planned |
