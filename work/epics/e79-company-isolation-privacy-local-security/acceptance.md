---
epic_id: E79
title: Aislamiento por empresa, privacidad y seguridad local
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# Aceptación E79

## Estado de las pruebas

**Pendiente de implementación y ejecución.** Esta matriz describe qué debe probar el implementador; no es un recibo de aceptación. La línea base observada está en el [registro de auditoría](../../../governance/pilot-readiness-2026-09-12.md).

## Matriz requisito → caso → evidencia

| Caso | Requisito / historia | Escenarios exigidos | Evidencia |
|---|---|---|---|
| AT-E79-001 | REQ-E79-001 / S79.1 | Positiva: seleccionar A, cambiar a B y reanudar A. Negativas: mismo nombre con IDs distintos, ID inválido, symlink fuera de raíz y selección ambigua. | Todas las entradas obtienen el mismo contexto validado y muestran la empresa activa sin exponer rutas privadas. |
| AT-E79-002 | REQ-E79-002 / S79.2 | Positiva: dos empresas con categoría/herramienta y nombres idénticos conservan valores distintos. Negativas: ID de B con sesión de A, contexto omitido, cache caliente y dos instancias. | Pruebas verifican cero lectura/escritura cruzada por API y conversación; cada consumidor del inventario tiene evidencia. |
| AT-E79-003 | REQ-E79-003 / S79.3 | Positiva: legado de una empresa confirmado y legado mixto resuelto explícitamente. Negativas: cancelación, interrupción, dos nombres iguales y relaciones sin dueño. | Conteos/hashes e identidades se concilian antes/después y una repetición no duplica registros. |
| AT-E79-004 | REQ-E79-004 / S79.4 | Positiva: navegador y cliente local autorizados. Negativas: archivo hermano, symlink, origen ajeno, Host ajeno, token ausente, cuerpo excesivo y lectura lenta. | Pruebas de HTTP real confirman rechazo y ausencia de contenido sensible; no basta invocar sólo el manejador. |
| AT-E79-005 | REQ-E79-005 / S79.5 | Positiva: autorización acotada y uso de datos sintéticos. Negativas: rechazo, cambio de empresa/proveedor/alcance y solicitud de borrado fuera del control local. | El empresario puede explicar dónde queda y a quién se envía su información; docs y comportamiento coinciden. |
| AT-E79-006 | REQ-E79-006 / S79.6 | Positiva: soporte recibe versión y error suficientes. Negativas: marcadores ficticios de secreto en nombres, logs, memoria y rutas nunca salen por el canal no autorizado. | Escaneo y prueba negativa muestran cero filtraciones del fixture y todos los rechazos conservan datos aprobados. |

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
