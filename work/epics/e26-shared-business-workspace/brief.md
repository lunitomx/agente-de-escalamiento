# E26 — Workspace Empresarial Compartido Local-First

**Estado:** Complete
**Fecha:** 2026-08-26
**Prioridad:** P0

## Resultado

Permitir que varios colaboradores trabajen sobre una misma carpeta empresarial
sin convertir ScaleUp en una plataforma cloud. Los documentos Markdown/YAML son
la fuente compartida y legible; cada computadora mantiene fuera de esa carpeta
su propio índice SQLite, reconstruible y descartable.

## Problema

Una base SQLite no debe sincronizarse mediante Drive: el archivo, WAL, locks y
copias en conflicto pueden corromperse o divergir. A la vez, pedir PostgreSQL,
una API u OAuth contradice la experiencia para empresarios no técnicos.

## Decisión de producto

El usuario comparte una carpeta normal mediante Drive Desktop, Dropbox, OneDrive
o equivalente. ScaleUp no implementa el proveedor: observa esa carpeta local,
valida sus archivos, genera un índice privado por equipo y guía la colaboración
en lenguaje natural desde Claude o Codex.

## Valor para el empresario

- Una memoria empresarial portable, auditable y sin dependencia de un modelo.
- Colaboración por áreas sin compartir bases de datos ni credenciales.
- Incorporación de un nuevo equipo reconstruyendo el contexto desde archivos.
- Trabajo offline y convergencia cuando el proveedor termine de sincronizar.
- Conflictos visibles y recuperables, nunca sobrescrituras silenciosas.

## Métrica de éxito

Dos instalaciones limpias que abran la misma instantánea de la carpeta deben
reconstruir el mismo inventario empresarial confirmado, manteniendo sus bases
SQLite fuera de la carpeta compartida.
