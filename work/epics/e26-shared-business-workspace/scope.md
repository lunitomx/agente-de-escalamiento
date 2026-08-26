# E26 — Scope

## Dentro del alcance

### Carpeta empresarial compartida

```text
Empresa-ScaleUp/
├── scaleup-workspace.yaml
├── company/
├── areas/
│   ├── cash/
│   ├── people/
│   ├── strategy/
│   └── execution/
├── plans/
├── cadence/
├── decisions/
└── contributions/
    └── {area}/{unique-id}.yaml
```

`scaleup-workspace.yaml` contiene sólo `workspace_id`, versión de esquema y
nombre visible. No contiene secretos, credenciales ni rutas absolutas.

### Estado local por computadora

```text
{local_state_root}/{workspace_id}/escala.db
```

La base, sus archivos `-wal`/`-shm`, locks, cachés y backups nunca se crean
dentro de la carpeta compartida. Se separan `workspace_root` y
`local_state_root`; la base implementada por E22 se migra conservando datos.

### Modelo de colaboración

- Markdown/YAML confirmado es la fuente de verdad portable.
- Contribuciones nuevas son append-only, con ID único, autor/rol, área, fecha,
  procedencia y estado de confirmación.
- Los documentos canónicos tienen responsable; una propuesta ajena no los
  sobrescribe hasta confirmación explícita.
- Datos privados del humano y secretos permanecen locales.
- El índice registra hash, ruta, procedencia y versión para detectar altas,
  cambios, renombres y bajas.
- Los conflictos del proveedor o de `base_hash` se conservan completos y se
  presentan para reconciliación.
- Una base perdida puede reconstruirse determinísticamente desde los archivos.

## Fuera del alcance

- PostgreSQL, servidor o API multiusuario de ScaleUp.
- OAuth o integración directa con Google Drive/Dropbox/OneDrive.
- Sincronización propia, edición simultánea en tiempo real o control de acceso.
- Compartir SQLite, WAL, SHM, locks, cachés o backups.
- Afirmar permisos por rol: el acceso real sigue siendo responsabilidad del
  proveedor de carpeta.

## Criterios de aceptación

1. Ningún SQLite ni sidecar aparece debajo de `workspace_root`.
2. Dos bases locales construidas desde la misma instantánea producen el mismo
   inventario/digest de conocimiento empresarial confirmado.
3. Un contador y un director pueden aportar a Cash y Execution sin pisarse.
4. Un conflicto conserva ambas versiones y pide reconciliación; no gana por
   “última escritura” silenciosa.
5. Una instalación nueva reconstruye memoria útil sin historial de chat ni DB.
6. El flujo completo funciona en lenguaje natural en Claude y Codex.
7. La documentación explica cómo compartir la carpeta con un proveedor común,
   sin presentar esa guía como integración nativa de ScaleUp.

## Dependencias

- E22 — Memoria Empresarial Integrada.
- E23 — Contexto Humano Consentido sólo para separar claramente lo personal;
  E26 puede implementar su núcleo sin esperar el resto de E23.
