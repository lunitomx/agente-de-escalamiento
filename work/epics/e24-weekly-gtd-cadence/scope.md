# Epic Scope: E24 — Cadencia Semanal GTD

**Status:** Complete
**Dependencies:** E22; E23 si existe perfil humano
**Tamaño:** L

## Outcome

Tras Welcome y un plan suficiente, ScaleUp ofrece una cadencia semanal opt-in
que revisa la semana anterior y prepara la siguiente mediante principios GTD.

## In Scope

- Configuración: día, zona horaria, duración, dueño y opción de parar.
- Revisión: resultado, cambio, bloqueo y renegociación.
- GTD: resultado deseado, proyecto, siguiente acción, waiting-for y someday.
- Relación con OPSP, prioridades, tareas y memoria confirmada.
- Check-in al abrir ScaleUp y sugerencia de recordatorio nativo si se pide.
- Automatizaciones recurrentes siempre propuestas: propósito, frecuencia, datos mínimos,
  capacidad del host, alternativa manual y aceptación explícita antes de activar.
- Historial local, métricas personales y edición/borrado.

## Out of Scope

- Enviar correo, SMS, WhatsApp, push o crear eventos directamente.
- OAuth, Calendar API o plataforma de tareas.
- Supervisar empleados, calificar productividad o automatizar decisiones.

## Reglas no negociables

1. Cadencia opt-in, pausada con una frase.
2. Un recordatorio, investigación recurrente o cualquier automatización es una sugerencia: ScaleUp no la activa, ejecuta ni afirma haberla ejecutado sin aceptación explícita del usuario.
3. La siguiente acción debe ser concreta y tener dueño; se pregunta si falta.
4. La revisión es apoyo, no vigilancia.

## Historias

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S24.1 — Contrato de cadencia y estados GTD | M | Modelo verificable y límites de opt-in. |
| 2 | S24.2 — Alta de revisión semanal tras Welcome | M | Configuración natural y reversible. |
| 3 | S24.3 — Conversación de revisión y siguiente acción | L | Bucle semanal conectado al plan. |
| 4 | S24.4 — Sugerencias de recordatorio nativo del host | M | Guía segura, sin OAuth ni falsa automatización. |
| 5 | S24.5 — Historial, evaluación y recuperación | M | Evidencia longitudinal, privacidad y E2E. |
| 6 | S24.6 — Automatizaciones recurrentes consentidas | M | Catálogo opt-in, propuesta/rechazo/edición y límites del host. |

## Acceptance Criteria

- [x] Activar, pausar y editar la cadencia por lenguaje natural.
- [x] Una sesión nueva detecta revisión vencida sin afirmar que notificó.
- [x] Cada semana conserva resultado, bloqueo y siguiente acción confirmados.
- [x] Sin plan/prioridad, guía primero al contexto mínimo.
- [x] Ninguna automatización queda activa sin aceptación explícita, propósito, frecuencia y forma de detenerla visibles.
