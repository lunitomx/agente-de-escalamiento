---
epic_id: E65
title: Compilador de procedimientos y MVP de seis intervenciones
status: planned
depends_on: [E64, E49, E52]
related: [E55, E56, E44]
---

# Scope E65

## Objetivo

Convertir nodos aprobados en procedimientos internos que guían una conversación y producen una decisión/artifacto verificable. El MVP demuestra el ciclo diagnóstico→plan→ejecución→revisión sin exponer una lista de comandos.

## Dentro

- Contrato tipado con trigger, non-trigger, inputs, entrevista, pasos, reglas, warnings, salida, criterios de aceptación, estado, handoff y evidencia.
- Compilador/validador de procedimientos desde ontología aprobada.
- Seis procedimientos: diagnóstico, OPPP, Vision Summary, prioridad trimestral, ritmo de reuniones y revisión trimestral.
- Integración con E49 para evidencia/ruta, E52 para consentimiento y E55 cuando haya fuentes múltiples.
- Salida obligatoria: artifacto, supuestos, preguntas abiertas, dueño, KPI, Who/What/When y cadencia.

## Fuera

- Crear skills públicos nuevos o reemplazar la puerta `escala` de E56.
- Compilar todo People/Strategy/Execution/Cash; eso es E69 después de E68.
- Automatizar decisiones de personal, dinero o estrategia sin confirmación humana.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S65.1 Contrato | Schema/fixtures de procedimiento válido e inválido. |
| 2 | S65.2 Compilador | Traza nodo→procedimiento y bloquea inputs no aprobados. |
| 3 | S65.3 Diagnóstico | Selección de restricción primaria o evidencia faltante. |
| 4 | S65.4 OPPP/Vision | Artefactos detallados, no escala Likert como sustituto. |
| 5 | S65.5 Prioridad/ritmo | Plan de 90 días y cadencia verificable. |
| 6 | S65.6 Revisión | Nueva iteración sin causalidad inventada. |

## Criterios de terminación

- Cada procedimiento cumple el contrato completo y conserva su evidencia.
- Ninguna respuesta de empresa se inventa; incertidumbre y preguntas abiertas aparecen en la salida.
- El ciclo MVP concluye con responsable, métrica y siguiente revisión.
- Pruebas positivas, negativas y de falta de datos pasan antes de E67.

## Handoff y riesgos

Entrega capacidades internas a E67 y registros de decisión a E44. No permite que formularios o scoring reemplacen una entrevista de detalle.
