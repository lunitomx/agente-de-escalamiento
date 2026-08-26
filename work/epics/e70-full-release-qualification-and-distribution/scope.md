---
epic_id: E70
title: Calificación total y gate de distribución
status: planned
depends_on: [E36, E42, E68, E69]
---

# Scope E70

## Objetivo

Tomar una decisión humana de distribución basada en evidencia de cobertura, fidelidad, privacidad local, instalación, límites conocidos y disposición explícita de derechos.

## Dentro

- Matriz `source_id → node_id → procedure_id → capability_id → test_id → release_status`.
- Validación de instalación limpia de ambos adaptadores y experiencia de puerta única.
- Verificación de invariantes local-first: estado local, SQLite no compartido, carpeta sincronizada sólo como intercambio de archivos y sin conectores/OAuth.
- Dry run de export limpio, inventario de dependencias/terceros y escaneo de corpus/derivados denegados.
- Evidencia de aceptación humana, limitaciones conocidas, huecos externos y decisión de publicar/no publicar.

## Fuera

- Publicar automáticamente tras pasar un test.
- Resolver derechos por inferencia, borrar historia Git o emitir opiniones jurídicas.
- Convertir la distribución en un servicio hospedado o sincronización multiwriter.
- Introducir funcionalidad nueva para mejorar el resultado del gate.

## Historias y secuencia

| Orden | Historia | Entrega verificable |
|---:|---|---|
| 1 | S70.1 Matriz de release | Trazabilidad completa y estado de cada eslabón. |
| 2 | S70.2 Instalación | Recibos de instalación limpia y rutas empresariales. |
| 3 | S70.3 Local-first | Pruebas de invariantes de datos/SQLite/carpeta. |
| 4 | S70.4 Frontera/IP | Clean export y disposición de derechos explícita. |
| 5 | S70.5 Aceptación | Lista de límites y decisión humana registrada. |

## Criterios de terminación

- Matriz completa, cero hallazgos críticos y resultados reproducibles.
- Clean export libre de corpus y derivados denegados.
- La documentación no promete capacidades ni cobertura no demostradas.
- Existe una decisión explícita de no publicar o de publicar con la revisión de derechos y aceptación aplicables.

## Handoff y riesgos

E70 es un gate de decisión, no una autorización automática. Cualquier hallazgo crítico devuelve el trabajo a la épica propietaria y conserva evidencia del bloqueo.
