---
epic_id: E86
title: ESCALA para el dueño — un minuto, una puerta, una decisión
status: active
jira_key: "ESCALA-68"
closure_disposition: active
created: 2026-09-30
updated: 2026-09-30
depends_on: []
related: [E82, E83, E84, E85]
source: work/audits/escala-52-auditoria-usuario-final.md
---

# Scope E86

## Objetivo

Que un dueño no técnico reciba su primera recomendación accionable en 3 pasos o menos, sin jerga, en la
plataforma que ya usa. Nace de la auditoría ESCALA-52 (scorecard: primer minuto y paridad en rojo).

## Decisión del dueño (2026-09-30)

- Abrir esta épica con las historias propuestas en §4 de la auditoría.
- **Todo el grupo de accountability hará las pruebas** con usuarios reales (guion §5 de la auditoría).

## Historias

Numeradas en el orden sugerido por la auditoría (baratas y visibles primero; la medición real a la mitad
para no invertir a ciegas en instalación y paridad).

| Historia | Jira | Entrega (hallazgos) | Tam. | Criterio verificable | Estado |
|---|---|---|:---:|---|---|
| S86.1 | ESCALA-69 | Cero comandos visibles (Q2 + Q4) | 2 | `grep '/escala-' escala-skills/*/SKILL.md` = 0 salvo `escala`, con test; `update.sh` deja 1 skill `escala*` | done |
| S86.2 | ESCALA-70 | Lenguaje del dueño (Q1 + A5) | 3 | Test sobre textos del dueño falla con People/Strategy/Execution/Cash/CCC/BHAG/SWT/OPSP/Deep Dive sin traducción | done |
| S86.3 | ESCALA-71 | Errores con salida (A1 + A2) | 3 | Test por módulo con fallo simulado; ningún `message` dice "tu Claude" | planned |
| S86.4 | ESCALA-72 | Puerta que conoce todo (S2) | 5 | Cada procedimiento `keep` alcanzable desde una frase del dueño; "bajaron mis ventas" → Strategy | planned |
| S86.5 | ESCALA-73 | Diagnóstico que termina en acción (S4) | 3 | Último mensaje con acción, responsable y fecha + oferta de anotarlo en la hoja | planned |
| S86.6 | ESCALA-74 | Prueba con dueños reales (§5) | 2 | Sesiones con el grupo, métricas llenas | planned |
| S86.7 | ESCALA-75 | Hoja con menos pegado (Q3 + S3) | 5 | ≤1 pegado por sección; cero preguntas de fecha | planned |
| S86.8 | ESCALA-76 | Reunión proactiva (A3) | 3 | Con reunión en ≤3 días se ofrece una vez; "después" no se repite | planned |
| S86.9 | ESCALA-77 | Instalación de un paso (S1 corto plazo) | 5 | Máquina limpia: ≤3 pasos, 0 decisiones técnicas | planned |
| S86.10 | ESCALA-78 | Paridad y consentimiento (A4 + M2/M7 del spike) | 3 | Misma entrada y cierre en Claude y Codex, transcripciones guardadas | planned |

## Fuera de alcance

- Adaptador de ChatGPT (lo decide E85 con las pruebas M1–M3 del dueño).
- Escritura directa en la hoja (depende de M4/P2).
- Rediseño de tableros HTML; lógica de cálculo de Cash.

## Reglas heredadas

- Fixtures sintéticos; nunca datos reales del tracker, `.escala/` ni `.scaleup/`.
- Español llano con ejemplo real en todo lo que ve el dueño.
- Ningún comando nuevo para el dueño; la única puerta es `escala`.
