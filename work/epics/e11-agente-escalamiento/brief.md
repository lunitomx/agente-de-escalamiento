---
epic_id: "E11"
title: "Agente de Escalamiento — repositorio público"
status: "draft"
created: "2026-05-24"
---

# Epic Brief: Agente de Escalamiento — repositorio público

## Hypothesis
Para estudiantes de licenciatura de Eduardo Muñoz Luna que necesitan un asistente de escalamiento de negocios,
el "Agente de Escalamiento" es un agente de IA instalable en Claude Code, Hermes Agent y Codex CLI
que guía al emprendedor en las 4 decisiones estratégicas (Personas, Estrategia, Ejecución, Cash)
con una metodología inspirada en autores reconocidos del escalamiento de negocios.
A diferencia de tener acceso al repositorio interno de desarrollo, este repo público es anonimizado,
atribuye correctamente a los autores originales y puede ser instalado libremente por cualquier estudiante.

## Success Metrics
- **Leading:** Repo público creado con todos los skills scaleup-* migrados y anonimizados
- **Lagging:** Un estudiante puede instalar el agente siguiendo el README en < 10 minutos

## Appetite
M — 6 historias

## Scope Boundaries
### In (MUST)
- Skills completos de la categoría scaleup-* anonimizados y migrados al nuevo repo
- Atribución explícita a autores originales cada vez que se menciona una metodología
- README con instrucciones de instalación para Hermes, Codex CLI y Claude Code
- Repo público en la cuenta personal de Eduardo en GitHub

### In (SHOULD)
- Atribuciones referenciadas desde sección dedicada en README

### No-Gos
- No incluir contenido del repositorio interno de desarrollo (skills de Kokoro, RaiSE, etc.)
- No revelar que el agente se construyó desde contenido público
- No incluir datos de clientes reales ni información de negocio de MH Services

### Rabbit Holes
- Perfeccionar la documentación más allá de lo necesario para instalación funcional
- Agregar funcionalidades nuevas que no están en los skills originales
- Traducir todo el agente a inglés (el público es hispanohablante)

## Key Decisions
- **Nombre del repo:** `agente-de-escalamiento`
- **Dueño:** Cuenta personal de Eduardo en GitHub
- **Base:** Repo limpio desde cero (no fork), solo los skills scaleup-*
- **Nivel de anonimización:** Profunda — renombrar conceptos, eliminar marcas registradas, reescribir ejemplos
