# E22 — smoke de clientes reales

Evidencia reproducible del 2026-08-26 para el bundle v1.0.0 en instalaciones temporales. `commands.sh` instala cada plataforma en un directorio nuevo, copia sólo la puerta pública instalada a la ruta de discovery del proyecto y ejecuta el cliente no interactivo. El único dato usado es ficticio.

Ambos clientes descubrieron sólo `scaleup`, ejecutaron pausa → declaración segura → `sí` → `retomemos`, y devolvieron la declaración confirmada. Las respuestas grabadas no incluyen rutas, SQLite ni términos internos. La base local se creó dentro del proyecto temporal; su hash no se conserva porque el proyecto no es un artefacto de release.

Los JSONL son una transcripción depurada del output real. Rutas temporales, identificadores de sesión, firmas y listas de herramientas se sustituyeron por `<RUNTIME>` o se omitieron. El SHA-256 del raw de Claude queda como ancla en `claude.jsonl`. No se versionan transcripts raw porque contienen rutas temporales; no contienen ni se copiaron tokens, credenciales ni datos empresariales reales.

Reproduce con un directorio temporal explícito:

```bash
RUN_ROOT="$(mktemp -d /tmp/scaleup-e22-client-smoke.XXXXXX)" bash commands.sh claude
RUN_ROOT="$(mktemp -d /tmp/scaleup-e22-client-smoke.XXXXXX)" bash commands.sh codex
./verify.sh
```

`verify.sh` es offline: sólo comprueba los SHA-256 y el esquema de assertions. No llama a un modelo, instalador ni runtime.
