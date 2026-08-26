# Epic Scope: E23 — Contexto Humano Consentido

**Status:** Complete
**Dependencies:** E22 (memoria local y confirmada)
**Tamaño:** M

## Outcome

Ofrecer, tras Welcome o al pedirlo, un perfil de colaboración personal opcional
que haga más útil el coaching y mantenga cada dato bajo control del usuario.

## In Scope

- Rol y responsabilidades declarados por la persona.
- Preferencias: estilo, idioma, nivel de detalle y ritmo.
- Restricciones operativas: disponibilidad, horizonte y capacidad.
- Objetivo personal-profesional ligado a la empresa, si lo desea.
- Consentimiento por campo, vista, edición, borrado y proveniencia local.
- Proyección mínima para coaching, E24 y E21.

## Out of Scope

- Inferir personalidad, salud, identidad u otra categoría sensible.
- Perfiles de empleados, clientes o proveedores.
- Cloud, multiusuario, telemetría o decisiones automáticas.

## Reglas no negociables

1. Omitirlo no bloquea el coaching.
2. Una pregunta útil por turno y beneficio explicado antes de guardar.
3. “No lo guardes”, “cámbialo” y “bórralo” deben funcionar siempre.
4. Dato sensible/secreto no se propone a memoria: se ofrece generalizarlo.

## Historias

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S23.1 — Contrato de contexto humano y límites | M | Esquema mínimo, consentimiento y casos adversariales. |
| 2 | S23.2 — Conversación voluntaria posterior a Welcome | M | Intake natural, omisible y no técnico. |
| 3 | S23.3 — Gestión y recuperación mínima | M | Ver, cambiar, borrar y proyectar sólo lo pertinente. |
| 4 | S23.4 — Integración y evaluación de privacidad | M | Regresiones, E2E y documentación. |

## Acceptance Criteria

- [x] Welcome actual funciona si se omite el perfil humano.
- [x] Ningún campo persiste sin confirmación y propósito visible.
- [x] Edición/borrado afecta sesiones futuras y memoria recuperada.
- [x] E21/E24 reciben sólo la proyección necesaria.
