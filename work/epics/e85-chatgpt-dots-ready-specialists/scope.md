---
epic_id: E85
title: ESCALA en ChatGPT (dots) y especialistas listos para usar
status: planned
jira_key: "ESCALA-51"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E45, E67, E82]
---

# Scope E85

## Objetivo

Muchos usuarios de ESCALA usan ChatGPT. Ofrecerles ESCALA y sus especialistas privados (cash/financiero, execution, etc., ya definidos en `adapters/specialists/contract.json`) listos para usar en ChatGPT, evaluando **dots** (agentes siempre activos de OpenAI, anunciados en DevDay 2026-09-29).

## Hechos conocidos (2026-09-30)

- **Superficies objetivo (decisión del dueño, 2026-09-30):** ChatGPT **Work** y **Codex**. El chat normal de ChatGPT queda fuera.
- ChatGPT Work (lanzado 2026-07-09): agente que usa apps conectadas, divide la meta en pasos y entrega hojas, slides, docs o web apps; tiene soporte de plugins. No verificado: si puede instalar ESCALA ni si edita una Google Sheet existente.
- Codex: ESCALA ya tiene adaptador (E67).
- Dots: agentes siempre activos con computadora y navegador propios en la nube, conectados a >4,000 apps; disponibles para Pro y Business Premium, no en EEE/Suiza/Reino Unido.
- ESCALA hoy tiene adaptadores para Claude y Codex (E67); no para ChatGPT.

## Incógnitas (spike obligatorio antes de diseñar)

1. ¿Un tercero puede empaquetar y distribuir dots preconfigurados, o cada usuario crea el suyo con instrucciones?
2. Dónde viviría la carpeta local de la empresa si el dot corre en la nube; qué implica para la privacidad (E79).
3. ¿Cómo se empaqueta ESCALA para ChatGPT Work (plugin, instrucciones, app)? ¿Work puede escribir en el tracker de E82?

## Fuera

- Prometer disponibilidad en ChatGPT antes de verificar el mecanismo de distribución.
- Enviar datos de la empresa a la nube sin consentimiento explícito.

## Historias (borrador)

| Historia | Entrega | Tamaño | Estado |
|---|---|:---:|---|
| S85.1 | Spike: mecanismo de distribución de dots y alternativas en ChatGPT; implicaciones de privacidad | S | planned |
| S85.2 | Adaptador ChatGPT del punto de entrada ESCALA (según spike) | M | planned |
| S85.3 | Especialistas listos (cash, execution, …) en ChatGPT | M | planned |
