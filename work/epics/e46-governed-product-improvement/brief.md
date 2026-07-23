---
epic_id: "E46"
title: "Governed Product Improvement"
status: "planned"
depends_on: ["E42", "E43", "E44", "E45"]
supersedes: ["E24"]
created: "2026-07-23"
---

# E46 — Mejora gobernada del producto

## Hipótesis

Para el equipo que opera ESCALA, convertir señales repetidas de uso, resultados,
clases y bug reports en propuestas comprobables permite mejorar el producto sin
exponer datos empresariales ni dejar que el sistema se modifique solo.

A diferencia del auto-patch propuesto en E24, E46 exigirá evidencia redactada,
casos antes/después, aprobación humana, versionado y reversión probada.

## Métricas de éxito

- **Señal temprana:** una señal repetida se convierte en un problema
  reproducible sin identidad ni datos empresariales.
- **Resultado:** una propuesta aprobada mejora sus casos conocidos sin romper
  los demás comportamientos protegidos.
- **Guardrail:** cero cambios automáticos a skills, prompts, código, memoria
  canónica o publicación.

## Tamaño

M — seis historias que prueban un ciclo real completo antes de habilitar una
segunda mejora.

## Dentro

- Señales locales desde bugreport, resultados de E44 y aprendizaje de clases.
- Redacción y minimización de datos antes de revisar patrones.
- Propuestas con problema, evidencia, cambio sugerido y medida esperada.
- Casos antes/después y gates contra regresiones.
- Aprobación humana, versión, reversión y medición posterior.

## No-Gos

- No entrenar modelos con información de empresarios.
- No enviar telemetría ni reportes por internet automáticamente.
- No aplicar cambios por cron, post-sesión o consenso de agentes.
- No modificar el producto en producción sin aprobación humana.
- No reabrir el auto-patch de E24.

## Rabbit Holes

- Tratar cada queja como una mejora del producto.
- Crear un sistema central de perfiles empresariales.
- Promover una propuesta que solo mejora un caso aislado.
- Confundir que una prueba pasó con que un empresario aceptó el cambio.
