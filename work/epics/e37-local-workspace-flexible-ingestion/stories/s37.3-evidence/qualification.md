# S37.3 Qualification Receipt

## Result

`PASS` en una carpeta temporal ordinaria que representa una carpeta de Drive o
OneDrive sincronizada. No se usó API cloud, OAuth, watcher, runtime hosted ni
SQLite sincronizado. El commit calificado es
`3a9b36b6c60d8239289d432cf7330dbff6eb4b25`.

## Local run

La carpeta contenía dos CSV, un workbook corrupto, una extensión desconocida,
un archivo sobredimensionado, un directorio y un symlink. La salida segura fue:

```json
{
  "absolute_root_in_receipt": false,
  "changed_csv": "accepted",
  "changed_identity": true,
  "cloud_api_used": false,
  "exchange_names_unchanged": true,
  "first_csv": "accepted",
  "ledger_entries_after_change": 5,
  "only_csv_bytes_changed": true,
  "report_written": true,
  "second_csv": "duplicate",
  "sqlite_created": false,
  "first_failure_codes": {
    "big.csv": "source_too_large",
    "broken.xlsx": "source_unreadable",
    "link.csv": "entry_symlink",
    "misterio.bin": "format_unsupported",
    "nested": "entry_directory",
    "target.csv": "profile_ready",
    "ventas.csv": "profile_ready"
  }
}
```

El primer scan acepta `ventas.csv`; el segundo devuelve `duplicate` con el
mismo source ID y no cambia el ledger. Después de modificar un byte, el tercer
scan acepta una identidad nueva y conserva las anteriores. Los documentos no
se mueven ni borran, el symlink permanece symlink, SQLite no se crea y el
receipt no contiene el root temporal.

## Focused quality gates

- `rai gate check gate-tests --scope tests/test_workspace_inbox.py` — PASS
- `rai gate check gate-lint` — PASS
- `rai gate check gate-format` — PASS
- `rai gate check gate-types` — PASS

## Boundary and ledger

El receipt prueba S37.3, no el ledger maestro. Las declaraciones E37 siguen
`unproved` hasta el cierre de E37; esta evidencia deja listos para promoción
REQ-E37-006 (inbox idempotente filesystem-only) y REQ-E37-007 (reportes seguros
para fallos).
