---
epic_id: "E47"
title: "Coherencia del viaje instalado: diseño"
status: "designed"
created: "2026-08-09"
---

# E47 — Diseño técnico

## Hallazgos de Gemba

1. La CLI de RaiSE resuelve su base desde `RAI_HOME` o `~/.rai/raise.db`. En Codex workspace-write, una transacción real sobre esa base devuelve `readonly database`, aunque la base por proyecto `.raise/rai/raise.db` exista.
2. `raise_session_open` por MCP reporta la misma base saludable. Por tanto, MCP es la vía operativa de Codex; no un permiso ampliado a la carpeta global.
3. `rai worktree register` crea `escala_coaching.egg-info/` al provisionar y luego falla porque detecta ese resultado como drift. La lista `.worktreeinclude` propaga `.codex/`, pero el runtime sigue usando `.mcp.json` rastreado con un comando bare.
4. `install.sh` solo instala symlinks de skills y el paquete editable. No materializa los recursos esperados por `escala-strategy-opsp`.
5. El skill OPSP solo describe ocho campos conversacionales y rutas `.escala/` inexistentes; la persistencia útil ya tiene DAO de worksheets y representación parcial de estrategia en `escala_server`.
6. El skill bugreport actual prohíbe leer el chat; eso impide precisamente un reporte contextual. Su contrato genera JSON, no el Markdown confirmado solicitado.

## Arquitectura por historias

### S47.1 — Workspace Codex/MCP

Crear una capa de contrato comprobable para detectar runtime Codex, priorizar `rai-workspace` MCP y convertir el caso de base read-only en una instrucción breve. Corregir el provisionador para que no deje `*.egg-info` visible y para que use una configuración MCP autocontenida con ruta absoluta o runtime comprobado.

### S47.2 — Instalación y recursos

Definir una única raíz de recursos instalada, migrar instalaciones existentes de forma idempotente e instalar/copiar recursos requeridos junto con skills. Probar las tres superficies de skill para evitar deriva.

### S47.3/S47.4 — OPSP

Definir un modelo Pydantic para columnas, horizontes de tiempo, filas de ejecución y accountability. Persistirlo mediante el DAO versionado, renderizar Markdown determinista y exponer reanudación/exportación local.

### S47.5 — Feedback

El activador solicita `bug` o `mejora`, usa únicamente el chat visible, redacta datos de empresa, muestra preview y guarda Markdown local tras consentimiento explícito. La importación al backlog permanece manual y separada.

### S47.6 — Calificación

Casos para instalación limpia/existente, sandbox Codex, error read-only, artefacto de workspace, modelo OPSP, reanudación/exportación, feedback negativo y aceptación humana pendiente.

## Controles incorporados tras revisión adversarial

- S47.1 inicia con una prueba reproducible de `rai worktree register` en un
  checkout limpio. Hasta que esa prueba aísle el origen, el `*.egg-info` es un
  síntoma observado, no una causa atribuida a un módulo concreto.
- S47.2 inventaría las copias, enlaces y consumidores de cada skill antes de
  migrarlos; no basta cambiar el origen canónico.
- S47.5 conserva consentimiento explícito y una política de redacción para
  texto del chat visible. La persona puede corregir o retirar contenido antes
  de que se guarde el Markdown.

## Límites

- Jira funciona con la cuenta Eduardo Luna: Epic `ESCALA-1` y S47.1 `ESCALA-2`. Un servidor MCP ya iniciado puede conservar credenciales previas; se reinicia y verifica antes de usarlo para writes.
- La aceptación humana del OPSP y del feedback no se sustituyen con tests.
- La separación física de credenciales y base en RaiSE requiere cambio en el proyecto que posee `raise-cli`; aquí se evita depender de ese permiso.

### Machine
```yaml
modules_affected:
  - path: install.sh
    change: modify
  - path: .mcp.json
    change: modify
  - path: escala-skills/escala-strategy-opsp/SKILL.md
    change: modify
  - path: escala-skills/escala-bugreport/SKILL.md
    change: modify
  - path: escala_server/daos/
    change: modify
  - path: escala_server/executive/
    change: modify
  - path: tests/
    change: modify
decisions:
  - id: D1
    choice: "MCP-first en Codex"
    rationale: "MCP funciona con la base activa; CLI no puede escribirla dentro del sandbox."
    constraint: "No abrir directorios globales con secretos."
  - id: D2
    choice: "Corregir provisionado antes de ampliar cobertura funcional"
    rationale: "Un worktree no listo invalida pruebas y sesiones posteriores."
    constraint: "La limpieza debe ser propiedad del provisionador, no del usuario."
  - id: D3
    choice: "Estado OPSP tipado y renderer Markdown"
    rationale: "La conversación no es persistencia ni contrato de datos."
    constraint: "No completar decisiones sin evidencia del usuario."
constraints:
  - "TDD para cada cambio de comportamiento."
  - "Artifacts de work/ se agregan explícitamente porque el repositorio los ignora."
  - "Cambios de skills canónicos se reflejan en superficies instaladas verificadas."
```
