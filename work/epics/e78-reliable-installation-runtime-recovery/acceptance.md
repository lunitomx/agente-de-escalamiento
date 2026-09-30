---
epic_id: E78
title: Instalación, runtime y recuperación verificables
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# Aceptación E78

## Estado de las pruebas

**Pendiente de implementación y ejecución.** Esta matriz describe qué debe probar el implementador; no es un recibo de aceptación. La línea base observada está en el [registro de auditoría](../../../governance/pilot-readiness-2026-09-12.md).

## Matriz requisito → caso → evidencia

| Caso | Requisito / historia | Escenarios exigidos | Evidencia |
|---|---|---|---|
| AT-E78-001 | REQ-E78-001 / S78.1 | Positiva: instalar y ejecutar Welcome con user-site deshabilitado desde otra carpeta. Negativas: Python 3.10, dependencia ausente, PATH con otro Python y agente no instalado. | Un recibo muestra el mismo intérprete en instalación y primera operación; no se crean entornos adicionales. |
| AT-E78-002 | REQ-E78-002 / S78.2 | Positiva: extracción e instalación en directorio con espacios, ejecución de coaching y servidor. Negativas: falta de YAML/static/módulo, hash alterado y carpeta movida sin reparación. | Inventario, hashes, versión y recursos ejecutados pertenecen al mismo artefacto; no se declara funcional una variante incompleta. |
| AT-E78-003 | REQ-E78-003 / S78.3 | Positiva: V1 responde un valor de prueba, V2 otro y rollback vuelve a V1. Negativas: descarga interrumpida, candidato corrupto, activación fallida y argumentos faltantes. | Se observa la versión activa mediante su comportamiento e identidad, además de comprobar estado empresarial y plataforma preservados. |
| AT-E78-004 | REQ-E78-004 / S78.4 | Positiva: proceso real sirve health y guarda/recupera dato sintético. Negativas: app/DB ausentes, muerte inesperada, marker obsoleto y puerto ocupado. | El proceso desaparece al detenerlo y el estado posterior refleja la realidad; las pruebas limpian todos los procesos. |
| AT-E78-005 | REQ-E78-005 / S78.5 | Positiva: snapshot durante escrituras y restauración en ubicación nueva con igualdad de datos confirmados. Negativas: corte a mitad, WAL pendiente, corrupción y permisos. | Recibo de restauración compara datos/esquemas y no sólo existencia del ZIP; datos reales y backups no entran en Git. |
| AT-E78-006 | REQ-E78-006 / S78.6 | Positiva: instalar → ejecutar → guardar → reiniciar → actualizar → recuperar. Negativas: cada H01/H02/H05 reaparece sembrado y el diagnóstico lo identifica. | Recibo de integración con commit/hash y pruebas de no pérdida; documentación y comandos se ejecutan tal como están escritos. |

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
