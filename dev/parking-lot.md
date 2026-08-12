# Parking Lot

## From E10: Cross-Platform Distribution

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Dashboard web para ScaleUp | E10 scope | Low | Cuando haya usuarios activos fuera de Eduardo |
| API REST del coaching engine | E10 scope | Medium | Cuando se necesite integración con apps externas |
| Publicar skills como "tap" de Hermes | E10 scope | Low | Cuando el bundle sea estable y testeado |
| ScaleUp en Claude Desktop (MCP server) | E10 scope | Medium | Cuando Claude Desktop soporte MCP skills |

## From E36: Product Truth, IP Boundary & Governance

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Rewrite private Git history | E36 design | Low | Only after a backup, exposure assessment, migration plan, and explicit destructive-action authorization |
| Google Drive or OneDrive API/OAuth integration | E36 design | Low | Only if local synced folders are proven insufficient in a later product cycle |
| Hosted or multi-writer ESCALA runtime | E36 design | Rejected | Incompatible with the local-only product invariant; requires a new product decision |
| Automated legal approval of license posture | E36 design | Low | Human counsel defines the decision and evidence boundary |
| Overwrite the existing dirty public candidate repository | E36 gemba | Rejected | Replace only through a reviewed clean-export migration; never synchronize private history into it |

## From E37: Local Workspace & Flexible Ingestion

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| OCR for image-only PDFs | E37 design | Low | A real local sample proves text extraction is insufficient and privacy/performance gates are defined |
| Universal parser for every workbook/document variant | E37 design | Rejected | Replace with a new bounded adapter decision; unsupported inputs must remain explicit |
| Cloud Drive/OneDrive API or OAuth | E37 ADR | Rejected | Only after a new product decision changes the local-only invariant |
| Multi-writer shared SQLite | E37 ADR | Rejected | Requires abandoning installer-machine data authority and a new ADR |

## From product discovery: People and knowledge cartridges

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Consent-based DISC assessment and local director view | Product discovery | Medium | Define consent, named-person access, retention, non-diagnostic language, and a local-only qualification before E40/E42 |
| Credited knowledge cartridges from company trainings (starting with Cash / Humberto) | Product discovery | High | Obtain rights and formula validation, then qualify the cartridge adapter against synthetic and real local workbooks |

## From E39: Meeting and Team Intelligence

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Audio/video transcription and OCR | E39 design | Low | A local sample proves text transcripts are insufficient and a privacy/performance contract exists |
| Calendar, Slack, Teams, email or issue integrations | E39 design | Low | A new product decision changes the local-files-only boundary and defines credentials/consent |
| Psychological or performance inference from meeting language | E39 design | Rejected | Requires a separate ethical/product decision; E39 only reports observable evidence |

## From E43-E46: Agentic learning roadmap

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Centralized cross-company learning or model training | E46 design | Rejected | Requires a new product decision, data agreements, anonymization review, legal approval, and a change to the local-only boundary |
| Automatic application of skill, prompt, or code changes | E46 design | Rejected | E46 may prepare evidence and a reversible proposal; a named human must approve each promotion |
| Permanent multi-agent execution for ordinary questions | E45 design | Rejected | Only reconsider if a measured pilot proves more business value than its added time and complexity |

## From E47: Coherencia del viaje instalado (audit-driven tangents, 2026-08-11)

| Item | Origin | Priority | Promotion Condition |
|------|--------|----------|-------------------|
| Consolidar catálogo escala-*/scaleup-* (62 + 39 skills, parcialmente duplicados) | Auditoría de producto vs. LifeOS | High | Aplicar el criterio Bitter Pill (¿un modelo con memoria real haría innecesario este skill?) a cada uno; fusionar al core Python o eliminar |
| ~~Decidir un solo repo de trabajo canónico entre ScaliingUPAI desarrollo y agente-de-escalamiento~~ — **RESUELTO 2026-08-11**: ScaliingUPAI desarrollo es el canónico (87 commits únicos vs. 1 en el otro clon). El commit único del otro clon (atribución Alan Miltz/Humberto Martínez Barón en escala-cash-*) fue cherry-picked; ambos clones fueron sincronizados y pusheados a `origin/main`. | Auditoría E47 | — | Cerrado |
| Evaluar Agent Plugins 1.0 (spec AAIF/Google: empaqueta Agent Skills + MCP en un manifest portable) para distribuir el catálogo escala-*/scaleup-* fuera de Claude | Investigación externa, sesión 2026-08-11 | Low | Solo después de que la consolidación Bitter Pill del catálogo defina qué skills sobreviven — no empaquetar antes de podar |
| Confirmar/rechazar el fix de visibilidad de `rai graph query` cross-repo en raise-commons (rama `fix/graph-query-cross-repo-gate`, commit `d0dc7bc11`, sin push) | Hallazgo lateral E47 (fuera de alcance del producto) | Low | Revisar cuando se trabaje en raise-commons directamente — no bloquea ESCALA |
| `governance/guardrails.md` no está trackeado en git pero varios tests lo leen como si existiera | Higiene de working tree detectada durante E47 | Medium | Comitear el archivo o quitar la dependencia de los tests que lo leen |
| Extender persistencia de OPSP (S47.4) a los mirrors `scaleup-strategy-opsp` en `.agents/.claude` | S47.4 (escala-skills solamente) | Low | Cuando se decida la consolidación de catálogo arriba — evita duplicar trabajo dos veces |
| Skills marcados como "aptos para compartir" (`escala-cash*`, `escala-rhythm-setup`) citan al libro/autor por nombre ("Verne recomienda", "Scaling Up / Gazelles", "score Rockefeller") — `governance/public-boundary.yaml` sí tiene reglas para bloquear esas palabras, pero nadie ha corrido el verificador sobre el contenido actual | Sesión 2026-08-11, revisión de límite público | Low (uso interno por ahora, solo bloquea si se comparte hacia afuera) | Antes de cualquier exportación/publicación real: reescribir esas menciones sin atribución literal y correr `scripts/check_public_boundary.py` hasta que pase limpio |
| Retrospectiva de E47 no existe como archivo aunque un commit dice "close epic" — carpeta `work/epics/e47-workspace-opsp-feedback/` no tiene `retrospective.md` | Auditoría de sesión 2026-08-11 | Low | Generar el archivo de cierre o reabrir la épica si sigue en progreso |
