---
epic_id: E81
title: Piloto empresarial de 3–5 a 20 participantes y soporte medible
document_status: ready_for_review
epic_status: planned
created: 2026-09-12
---

# Aceptación E81

## Estado de las pruebas

**Pendiente de implementación y ejecución.** Esta matriz describe qué debe probar el implementador; no es un recibo de aceptación. La línea base observada está en el [registro de auditoría](../../../governance/pilot-readiness-2026-09-12.md).

## Matriz requisito → caso → evidencia

| Caso | Requisito / historia | Escenarios exigidos | Evidencia |
|---|---|---|---|
| AT-E81-001 | REQ-E81-001 / S81.1 | Positiva: cada combinación anunciada enlaza a recibo vigente. Negativas: etiqueta 'windows' de fixture Linux, recibo de otro hash y capacidades no distribuidas no califican. | Protocolo y matriz versionados; E42/E68 conservan su autoridad y no se exige cerrar un piloto para poder preparar su protocolo. |
| AT-E81-002 | REQ-E81-002 / S81.2 | Positiva: soporte reproduce el fallo con fixture y metadata mínima. Negativas: negarse a compartir funciona y el reporte no incluye datos/credenciales/rutas privadas. | Runbook probado con incidentes sembrados y registro que distingue autoservicio de ayuda humana. |
| AT-E81-003 | REQ-E81-003 / S81.3 | Positiva: registros de sesiones reales y artefactos locales recuperados. Negativas: abandono, no consentimiento o caso inconcluso quedan registrados, no sustituidos por fixtures. | Decisión explícita de pasar/iterar con n=3–5, asistencia y criterios congelados; disponibilidad humana sigue siendo dependencia externa. |
| AT-E81-004 | REQ-E81-004 / S81.4 | Positiva: cohorte completa con denominadores y evidencia de ambas sesiones. Negativas: no iniciados y asistidos no cuentan como éxitos autónomos; no observados no se convierten en recuperaciones exitosas. | Dataset privado mínimo y reporte agregado con valores observados, objetivos y excepciones separados. |
| AT-E81-005 | REQ-E81-005 / S81.5 | Positiva: evaluación humana puede explicar por qué la acción fue útil. Negativas: respuesta convincente sin evidencia, conclusión errónea o ausencia de ventaja no se promueven. | Comparación reproducible y limitada; si no hay muestra comparable, se declara pendiente y no se inventa superioridad. |
| AT-E81-006 | REQ-E81-006 / S81.6 | Positiva: decisión enlaza criterios congelados y resultados reales. Negativas: sólo fixtures, menos de veinte sin explicación o datos omitidos impiden afirmar cohorte de veinte calificada. | Evaluación completa, aceptación real y backlog actualizado; readiness del producto se mantiene bloqueada si los objetivos o reparaciones no se cumplieron. |

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

Los objetivos de adopción son propuestas congelables antes de reclutar, no cifras observadas. Un resultado por debajo del objetivo debe aparecer en la decisión de iterar/detener y mantener bloqueada la ampliación. El informe distingue aceptación de la evaluación y aceptación del producto.
