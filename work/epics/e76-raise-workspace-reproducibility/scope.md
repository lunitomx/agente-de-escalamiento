---
epic_id: "E76"
title: "RaiSE workspace reproducibility"
status: "complete"
created: "2026-08-27"
priority: "P0-development-enabler"
---

# E76 — Recuperación reproducible del workspace RaiSE

## Problema

El producto ESCALA no depende de RaiSE en la máquina del empresario, pero este
repositorio sí declara usar su metodología. La auditoría encontró ausencia de
manifest/configuración de proyecto, grafo sin construir y workspace sin
registro. Esto impide repetir sus gates y vuelve ambiguo qué configuración es
producto, qué configuración es de desarrollo y qué es opcional.

## Objetivo

Dejar un contrato de desarrollo RaiSE mínimo, reproducible y documentado para
Codex, sin enviar datos de empresa, sin crear un servidor y sin crear un venv
adicional cuando el proyecto ya dispone de `.venv`.

## Dentro

- Diagnóstico raíz de por qué `rai init` no deja el manifest requerido en este
  checkout y una reparación reproducible.
- Configuración mínima del proyecto y del workspace Codex que no contenga
  secretos ni rutas personales.
- Grafo local construible desde archivos versionados y una política clara de
  cuándo reconstruirlo.
- Workflow/pipeline que cubra el ciclo usado en este repositorio, o declaración
  explícita de que el gate no aplica.
- Clasificación de MCP, Jira, Hermes y entornos como requerido, opcional o
  fuera de alcance; los opcionales no bloquean desarrollo local.

## Fuera

- Convertir RaiSE en dependencia del instalador de ESCALA.
- Crear `.venv-mcp` o cualquier entorno duplicado si `.venv` existente basta.
- Añadir secretos, conectores de terceros, Jira o servicios remotos sólo para
  eliminar un warning.
- Cambiar skills de negocio de ESCALA sin una necesidad demostrada.

## Historias

| ID | Historia | Estado | Termina cuando |
|---|---|---|---|
| S76.1 | Diagnóstico y contrato de inicialización | Complete | La causa de manifest/config faltantes está documentada y una instalación limpia es repetible. |
| S76.2 | Workspace mínimo Codex | Complete | La configuración necesaria queda versionada o generada de forma determinista sin secretos ni venv duplicado. |
| S76.3 | Grafo y pipeline verificables | Complete | El grafo se construye localmente y el workflow aplicable produce una verificación útil. |
| S76.4 | Gate y retrospectiva | Complete | `rai doctor` no tiene errores aplicables al contrato elegido y las excepciones opcionales están justificadas. |

## Criterios de terminación

- [x] Ningún requisito depende de infraestructura no autorizada o secreta.
- [x] El checkout nuevo sigue un único procedimiento reproducible.
- [x] La configuración distingue desarrollo RaiSE de instalación de producto.
- [x] No se crean entornos virtuales duplicados.
- [x] La retrospectiva enlaza cualquier warning residual con dueño y decisión.
