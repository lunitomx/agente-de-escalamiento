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
