# Auditoría de cierres E21–E31 — 2026-08-26

## Método RaiSE

Se revisaron los scopes/retrospectivas cerrados hoy, los commits `6462365` y
`a65bb90`, sus pruebas y las rutas de ejecución. También se ejecutó:

- `rai drift check coaching/router/conversation.py --format json`
- `rai drift check escala_server/evidence.py --format json`

No se encontraron clones ni hallazgos SAST en esos módulos; RaiSE sí marcó al
router como punto de alto acoplamiento histórico. Ese dato refuerza que el
siguiente cambio debe extraer un contrato común, no añadir otro flujo ad hoc.

## Matriz de cierre y huecos verificables

| Épica | Lo que sí quedó | Evidencia de hueco | Decisión E32 |
|---|---|---|---|
| E21 Board | Lente metodológica trazable sobre conocimiento E19 | `_board_turn` construye `BoardContextBuilder(PortableKnowledgeHandler())` sólo con el texto de la petición; no recibe perfil, plan, evidencia ni Accountability local. | Paquete de contexto empresarial para Board. |
| E22 Memoria | SQLite local, continuidad y consentimiento | La memoria no se compone como entrada del Board ni se convierte automáticamente en documento portable confirmado. | Lector de contexto mínimo, con procedencia. |
| E23 Contexto humano | Almacenamiento y proyección consentida | La ruta pública del Board no solicita `HumanContextStore.project("board")`; la proyección prometida no llega a ese consumidor. | Proyección explícita, auditable y opt-in. |
| E24 Cadencia | Compromisos/revisión GTD locales | Su siguiente acción y bloqueos no participan en la consulta ejecutiva salvo que la persona los vuelva a pegar. | Incluir resumen mínimo confirmado. |
| E25 Conectores | Guía conservadora, sin OAuth | No hay hueco: el límite de no ejecutar conectores sigue correcto. | Conservar frontera; sólo contenido/adjunto explícito. |
| E26 Workspace | Documentos syncables y SQLite local reconstruible | Sólo indexa raíces canónicas YAML/Markdown. `EvidenceStore` escribe `methodology_values` en SQLite y no emite contribución/canónico portable. | Evidencia aceptada → documento portable + reconstrucción. |
| E27 Diagnóstico | Narrativa antes de score | Notas y síntesis quedan en perfil local; no existe un paquete reutilizable para consulta ejecutiva. | Incluir síntesis confirmada en el lector. |
| E28 Runtime | Instalador y panel local en tres hosts | `scaleup-frontdoor` acepta únicamente un `message: str`; no hay contrato de adjunto explícito desde el host, por lo que E31 termina pidiendo una referencia textual. | Adaptador de adjunto sin rutas ni protocolo expuesto al usuario. |
| E29 Business Pulse | Datos locales, procedencia y estados honestos | Sólo consulta worksheets/perfil; no compone evidencia, Accountability ni contribuciones portables en una misma vista. | Consumir paquete común y mostrar huecos. |
| E30 Accountability | Sesiones, compromisos y patrones locales | Sus hechos confirmados no viajan al workspace ni llegan al Board sin reescritura manual. | Resumen portátil mínimo, nunca notas personales crudas. |
| E31 Evidencia | Preview/consentimiento por campo, fuente, vigencia | Las pruebas no cubren reconstrucción desde E26 ni adjunto real de host; las filas confirmadas viven sólo en SQLite. | Cierre de portabilidad, adjunto y consumo ejecutivo. |

## No se promueve como hueco

- OAuth, sincronización propia, scraping, acceso silencioso a Drive/Calendar o
  compartir SQLite: E25/E26 los excluyen deliberadamente y E32 los conserva
  fuera de alcance.
- Hallazgos históricos de lint global: son deuda previa y no prueban un hueco
  funcional de los cierres E21–E31.

## Conclusión

E32 es una única épica porque los tres cortes comparten el mismo contrato:
**contenido explícito → preview → confirmación → documento portable → contexto
con procedencia para consumidores**. Resolverlos por separado volvería a crear
fuentes de verdad paralelas.
