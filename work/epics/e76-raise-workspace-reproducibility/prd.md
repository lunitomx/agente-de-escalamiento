---
epic_id: "E76"
title: "PRD — RaiSE workspace reproducibility"
status: "active"
---

# PRD E76

## Usuario

La persona que desarrolla o audita ESCALA con Codex y necesita aplicar RaiSE de
forma consistente, sin que la herramienta interna altere el producto ni obligue
a instalar infraestructura empresarial.

## Resultado esperado

Puede clonar el repositorio, ejecutar el procedimiento de preparación, saber
qué controles RaiSE aplican y reproducir los gates locales. Los datos de
empresas continúan fuera de la configuración de desarrollo.

## Métricas

- Cero errores `rai doctor` que pertenezcan al contrato explícito.
- Cero secretos y cero rutas privadas en archivos versionados.
- Cero entornos virtuales adicionales creados por el flujo.
- Un build de grafo y un gate de pipeline reproducibles desde checkout limpio.

## Restricciones

No se considera éxito instalar Jira, Hermes, Claude MCP o servicios remotos si
no son necesarios para Codex/local. Cada advertencia residual debe quedar como
opcional o tener una historia activa con dueño.
