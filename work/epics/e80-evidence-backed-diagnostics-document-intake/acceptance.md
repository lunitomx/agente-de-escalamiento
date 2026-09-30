---
epic_id: E80
title: Diagnósticos honestos e ingreso de información útil
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# Aceptación E80

## Estado de las pruebas

**Pendiente de implementación y ejecución.** Esta matriz describe qué debe probar el implementador; no es un recibo de aceptación. La línea base observada está en el [registro de auditoría](../../../governance/pilot-readiness-2026-09-12.md).

## Matriz requisito → caso → evidencia

| Caso | Requisito / historia | Escenarios exigidos | Evidencia |
|---|---|---|---|
| AT-E80-001 | REQ-E80-001 / S80.1 | Positiva: datos comparables muestran indicador definido. Negativas: sólo un pilar, mezcla de periodos/unidades y ausencia total no producen salud global. | Contrato y ejemplos aprobables explican cada indicador sin tecnicismos ni falsa precisión. |
| AT-E80-002 | REQ-E80-002 / S80.2 | Positiva: plan válido muestra avance con etiqueta precisa. Negativas: ocho 'pendiente', whitespace, schema inválido y evidencia vencida nunca producen salud 100. | API y dashboard muestran el mismo significado y la limitación se entiende sin leer documentación técnica. |
| AT-E80-003 | REQ-E80-003 / S80.3 | Positiva: dos contextos incompatibles generan conclusión o pregunta distinta donde corresponde. Negativas: contexto omitido, ajeno o stale no personaliza ni inventa cifras. | Recibo enlaza afirmaciones empresariales a hechos autorizados o las etiqueta como hipótesis/orientación general. |
| AT-E80-004 | REQ-E80-004 / S80.4 | Positiva: PDF textual sintético y archivo tabular equivalente producen hechos conciliables. Negativas: escaneado, contraseña, truncado, excesivo y moneda/periodo ambiguos. | Fuente/página y confirmación acompañan al dato; ningún fallback convierte una limitación en éxito ficticio. |
| AT-E80-005 | REQ-E80-005 / S80.5 | Positiva: primera acción y reanudación una semana después con estado persistido. Negativas: usuario rechaza guardar, cambia empresa, corrige cifra o no aporta datos suficientes. | El recorrido conserva contexto útil y no inventa una decisión para cumplir el objetivo temporal del piloto. |
| AT-E80-006 | REQ-E80-006 / S80.6 | Positiva: mismo caso autorizado produce artefactos compatibles. Negativas: datos contradictorios, incompletos, placeholders y contexto cruzado son visibles y bloquean conclusiones dependientes. | Recibo de integración por artefacto/versión, con límites del modo standalone y de cada adaptador. |

## Recibo mínimo

Cada ejecución registra fecha UTC, commit completo, hash de artefacto, caso/requisito, modo (unitario, integración local, hardware limpio o sesión humana), plataforma/arquitectura y versiones relevantes, entrada sintética o referencia opaca autorizada, resultado esperado/observado, pass/fail/pending, razón y ubicación local de evidencia.

Registrar también dependencias usadas y límites: un mock de agente no cuenta como invocación del modelo, una etiqueta de plataforma no cuenta como ejecución en ese SO, un marker no cuenta como proceso vivo y un documento generado no cuenta como aceptación humana.

## Preparación y ejecución

1. Leer las pruebas existentes de los componentes listados en cada historia y reproducir el hallazgo asociado antes de cambiarlo.
2. Reutilizar el entorno del proyecto; no instalar dependencias globales ni crear venvs duplicados. Los entornos temporales de calificación deben estar aislados, identificados y limpiarse al terminar.
3. Usar fixtures sintéticos para código versionado; mantener datos empresariales y recibos identificables fuera de Git/export.
4. Ejecutar primero regresiones focalizadas y luego el recorrido de integración indicado. Aplicar lint, tipos y gates pertinentes a los archivos implementados.
5. Para hardware/agente real, consumir los protocolos E42/E68 y fijar artefacto/versiones. Un error de entorno queda como limitación, no como pass.
6. Cerrar servidores/procesos temporales; guardar resultados redactados y enlazar el requisito/historia.

## Decisión de cierre

No aprobar si una prueba falla, un requisito se omite, cambia la versión sin revalidación o falta evidencia externa exigida. Registrar qué falta y quién lo resuelve. No convertir una aceptación parcial en cierre total ni editar retrospectivamente el criterio para que el resultado pase.

E42 y E68 mantienen su cierre externo independiente. Los recibos de esta épica son entradas para esos gates y para el piloto E81; no los reemplazan.
