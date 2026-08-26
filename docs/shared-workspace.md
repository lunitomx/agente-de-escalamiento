# Carpeta empresarial compartida

ScaleUp puede trabajar con una carpeta normal sincronizada por el proveedor que
la empresa ya use. No instala Drive, Dropbox, OneDrive, OAuth, una API ni un
servidor.

## Para la persona que usa ScaleUp

1. Abre Claude Code o Codex dentro de la carpeta empresarial que quieres
   compartir.
2. Di: “Quiero compartir esta carpeta con mi equipo.”
3. Confirma la única pregunta. ScaleUp crea el manifiesto y las carpetas de
   documentos empresariales.
4. Comparte esa carpeta usando Drive Desktop, Dropbox, OneDrive o el servicio
   corporativo que ya administra tu equipo.
5. Cada colaborador abre la misma carpeta en su computadora y puede pedir:
   “Revisa la carpeta compartida.”

Los documentos confirmados viven en Markdown/YAML y se pueden leer sin
ScaleUp. Cada computadora conserva fuera de esa carpeta su propio SQLite,
cachés, copias y locks. Si esa base desaparece, ScaleUp puede reconstruirla
desde los documentos.

## Qué se comparte y qué no

| Se puede compartir | Nunca se comparte desde ScaleUp |
|---|---|
| Perfil/planes/decisiones confirmadas | SQLite, WAL, SHM, locks y backups |
| Contribuciones por Cash, People, Strategy o Execution | Contraseñas, tokens, claves privadas o secretos |
| Historial de conciliaciones confirmado | Contexto personal que no hayas confirmado |

La plataforma de archivos es quien controla accesos y permisos. Los roles de
ScaleUp describen responsabilidad editorial, no permisos técnicos.

## Conflictos

Una contribución no reemplaza un documento confirmado. Si se basa en una versión
anterior o el proveedor crea una copia en conflicto, ScaleUp conserva las
versiones, lo muestra como pendiente y espera una conciliación explícita. La
conciliación genera un nuevo documento confirmado y deja un registro de la
versión anterior y de las contribuciones resueltas.
