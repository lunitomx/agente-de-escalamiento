# Epic Scope: E25 — Guía de Contexto Conectado

**Status:** Complete
**Dependencies:** E22; E23 para preferencias; E24 como primer consumidor
**Tamaño:** M

## Outcome

ScaleUp recomienda fuentes externas apropiadas —por ejemplo, Drive para
documentos o Calendar para compromisos— sólo cuando el usuario necesita contexto
que no está en su workspace local.

## In Scope

- Catálogo: necesidad → tipo de fuente → conector sugerido.
- Detección conservadora de capacidades disponibles en el host.
- Propósito, dato mínimo, alcance, alternativa manual y salida.
- Guía para desidentificar nombres, importes, clientes y documentos.
- Límite de persistencia/indexación y consentimiento por contenido.
- Registro local de la decisión de conectar o no, sin tokens ni datos obtenidos.
- Recetas opt-in de revisión externa recurrente —por ejemplo, un SWT trimestral con Deep Research— que el host puede o no soportar.

## Out of Scope

- OAuth, SDK, APIs, ingestión, scraping o sincronización de Drive/Calendar.
- Ejecutar conectores, crear eventos o modificar archivos externos.
- Reemplazar políticas de privacidad del host/proveedor.

## Reglas no negociables

1. ScaleUp sugiere; host ejecuta y usuario autoriza.
2. Toda fuente y automatización es opcional, tiene alternativa manual/local y exige aceptación explícita antes de configurarse.
3. Secretos nunca se guardan/indexan; lo delicado exige minimización y permiso.
4. Permisos/retención/transferencia pertenecen al conector y proveedor.

## Historias

| Orden | Story | Tamaño | Resultado |
|:---:|---|:---:|---|
| 1 | S25.1 — Política de sugerencia y frontera de datos | M | Necesidad, mínimo dato y consentimiento. |
| 2 | S25.2 — Conversación de recomendación y anonimización | M | Guía no técnica y rechazo seguro. |
| 3 | S25.3 — Adaptadores de capacidad Claude/Codex | M | Recomendación honesta, sin invocar conectores. |
| 4 | S25.4 — Evaluación adversarial y documentación | M | Privacidad, regresiones y transparencia. |
| 5 | S25.5 — Recetas de revisión externa consentida | M | SWT/Deep Research como propuesta opcional, anónima y honesta sobre el host. |

## Acceptance Criteria

- [x] Drive/Calendar se sugieren por necesidad, nunca como requisito de Welcome.
- [x] La sugerencia deja claro que la conexión ocurre fuera de ScaleUp.
- [x] Dato delicado no llega a memoria/índice antes de anonimizar/autorizar.
- [x] Funciona en hosts sin conectores.
- [x] Una revisión SWT recurrente se propone, se acepta o se rechaza explícitamente; nunca se ejecuta ni se declara programada por ScaleUp.
