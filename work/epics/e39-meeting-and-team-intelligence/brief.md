# E39: Meeting and Team Intelligence — Brief

## Hypothesis

Si ESCALA puede recibir transcripts diarios y semanales tal como el empresario ya los guarda, identificar su contexto y extraer decisiones, acciones y señales con procedencia verificable, el director podrá revisar la salud de su equipo cada día sin depender de un formato único ni de un servicio hospedado.

## Outcome

Una empresa local puede dejar transcripts en una carpeta ordinaria (incluido un folder de Drive/OneDrive sincronizado), ejecutar el análisis en la máquina instaladora y obtener un resumen ejecutivo accionable con preguntas, bloqueos y tendencias, sin que la carpeta compartida se convierta en autoridad de datos.

## Success metrics

- 100% de los archivos aceptados tienen identidad estable e ingestión idempotente.
- Cada hecho extraído conserva fuente, rango de líneas y confianza; los hechos ambiguos quedan sin resolver.
- Los análisis de ritmo, tendencias y salud nunca convierten ausencia de evidencia en fallo personal ni inventan hallazgos negativos.
- Todos los reportes son locales, deterministas y redacted; ninguna SQLite ni worker hospedado es necesario.

## Appetite

Construir el MVP local de inteligencia de reuniones para una empresa sintética, con cuatro stories y siete requisitos del ledger maestro. No intentar entender lenguaje universal, grabar reuniones, enviar correo ni integrar calendarios cloud.

## Rabbit holes deferred

- Transcripción de audio/video y OCR.
- Integraciones OAuth, Slack, Teams, Google Calendar o servicios de issues.
- Inferencia psicológica o evaluación de desempeño de personas.
- Correlación con DISC y cockpit ejecutivo (E40).
- Instalador nativo y aceptación con empresarios reales (E41/E42).
