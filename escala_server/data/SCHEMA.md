# E19 Book Knowledge Schema

**Status:** Canonical for the E19 artifact and its current SQLite projection
**Source artifact:** `escala_server/data/book-knowledge.json`
**Generator:** `escala_server/data/book_parser.py`
**Ingester:** `escala_server/data/knowledge_ingester.py`

## Layers

E19 exposes one knowledge model through four representations:

1. The generated JSON artifact preserves chapters, stable source IDs and provenance.
2. `KnowledgeIngester` projects entities and directed relationships into SQLite.
3. Each ingested entity also creates a `book_knowledge` memory fact.
4. `KnowledgeHandler` exposes search, entity detail and contextual projections.

The JSON artifact is the lossless E19 interchange format. SQLite and API responses
are projections and do not preserve every JSON field.

## Current Dataset

| Item | Count / values |
|------|----------------|
| Chapters | 406: 65 level 1, 210 level 2, 131 level 3 |
| Entities | 42 |
| Entity types | 15 concept, 6 tool, 5 metric, 5 habit, 7 principle, 4 decision |
| Relationships | 59 directed edges |

These counts describe the checked-in `book-knowledge.json`; consumers should use
the arrays and `meta` counts rather than hard-code them.

## JSON Document

The root object has four required keys:

| Field | Type | Contract |
|-------|------|----------|
| `meta` | object | Source identity and entity/relationship counts. |
| `chapters` | array of Chapter | Flattened heading tree in source order. |
| `entities` | array of Entity | Curated book concepts and the four decision nodes. |
| `relationships` | array of Relationship | Directed links using Entity string IDs. |

### Meta

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| `source` | string | yes | Currently `scaling_up_llamaparse.md`. |
| `entities_count` | integer | yes | Must equal `len(entities)`. |
| `relationships_count` | integer | yes | Must equal `len(relationships)`. |

There is currently no `schema_version` or chapter count in `meta`.

### Chapter

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | integer | yes | Sequential, positive, unique within the artifact. |
| `title` | string | yes | Heading text after parser cleanup. |
| `level` | integer | yes | One of `1`, `2`, `3`. |
| `line_start` | integer | yes | One-based source line. |
| `line_end` | integer | yes | Greater than or equal to `line_start`. |
| `slug` | string | yes | Lowercase heading-derived lookup value. Not globally guaranteed unique. |
| `parent_id` | integer | no | ID of the nearest containing chapter; absent for roots. |

Chapters are a flattened hierarchy. `parent_id`, not array position, expresses
nesting.

### Entity

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `id` | string | yes | Stable artifact key; unique and used by relationship endpoints. |
| `name` | string | yes | Human-readable display name. |
| `type` | string enum | yes | `concept`, `tool`, `metric`, `habit`, `principle`, or `decision`. |
| `description` | string | yes | Curated description used by search and memory facts. |
| `keywords` | array of string | yes | Case-insensitive search terms. |
| `line_refs` | array of integer | yes | One-based evidence locations in the source Markdown. May be empty. |
| `chapter_ids` | array of integer | yes | References valid Chapter IDs. May be empty. |

Example shape:

```json
{
  "id": "example-concept",
  "name": "Example Concept",
  "type": "concept",
  "description": "A concise description.",
  "keywords": ["example"],
  "line_refs": [120],
  "chapter_ids": [8]
}
```

### Relationship

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `source` | string | yes | Existing Entity `id`; edge direction starts here. |
| `target` | string | yes | Existing Entity `id`; edge direction ends here. |
| `type` | string enum | yes | One of the relationship types below. |
| `weight` | number | yes | Greater than `0` and less than or equal to `1.0`. |
| `line_ref` | integer or null | yes | Optional source-line provenance for the edge. |
| `description` | string | yes | Human-readable rationale for the relationship. |

Current relationship types:

`applies_to`, `belongs_to`, `complements`, `contained_in`, `contains`,
`enables`, `guides`, `impacts`, `implements`, `improves`, `incorporates`,
`informs`, `is_a`, `is_tool_for`, `measures`, `mirrors`, `reinforces`,
`relates_to`, `serves`, and `supports`.

Relationships are directed. Consumers must not infer the reverse predicate.

## Integrity Invariants

- Every relationship `source` and `target` resolves to an Entity `id`.
- Every Entity `chapter_ids` value resolves to a Chapter `id`.
- `meta.entities_count` and `meta.relationships_count` match their arrays.
- Entity types and chapter levels stay within their declared enums.
- Relationship weights stay in `(0, 1]`.
- Chapter IDs remain sequential and source line ranges do not invert.
- The current integrity suite covers all four `decision` entities; it does not
  guarantee that every parsed chapter has a dedicated entity.

## SQLite Projection

### `entities`

| Column | SQLite type | Source |
|--------|-------------|--------|
| `id` | INTEGER primary key | Generated by SQLite; not the JSON Entity `id`. |
| `type` | TEXT not null | Entity `type`. |
| `name` | TEXT not null | Entity `name`. |
| `properties` | TEXT JSON | `description`, `keywords`, `line_refs`, `chapter_ids`. |
| `created_at` | TEXT | SQLite timestamp. |
| `updated_at` | TEXT | SQLite timestamp. |

The ingester uses exact `name` matching for entity idempotency. The database does
not define a unique constraint on `name`, and the JSON Entity `id` is not
persisted. Renaming an entity therefore creates a new logical record unless a
migration handles it.

### `relationships`

| Column | SQLite type | Source |
|--------|-------------|--------|
| `id` | INTEGER primary key | Generated by SQLite. |
| `source_entity_id` | INTEGER not null | SQLite Entity ID mapped from `source`. |
| `target_entity_id` | INTEGER not null | SQLite Entity ID mapped from `target`. |
| `relation_type` | TEXT not null | Relationship `type`. |
| `properties` | TEXT JSON | Currently only `{ "weight": number }`. |
| `created_at` | TEXT | SQLite timestamp. |

Idempotency is enforced in application code on the triple
`(source_entity_id, target_entity_id, relation_type)`. The table has indexes but
no foreign-key or unique constraints. JSON `description` and `line_ref` are not
persisted in the current projection.

### Memory Fact Side Effect

Each entity creates a memory fact with:

- `category`: `book_knowledge`
- `source`: `knowledge_ingester`
- `content`: entity type, name and description
- `tags`: the first five entity keywords

The graph idempotency contract does not by itself guarantee deduplication of
memory facts; consumers should not use fact count as the entity count.

## HTTP Projections

| Endpoint | Input | Success shape |
|----------|-------|---------------|
| `POST /api/knowledge/ingest` | Optional `json_path` | `{data: {entities_created, relationships_created, entities_skipped}, status}` |
| `GET /api/knowledge/search` | `q`, optional `type` | `{entities, count, status}`; each entity has DB `id`, `type`, `name`, `description`, `keywords`. |
| `GET /api/knowledge/entity/{entity_name}` | Exact name or simplified slug | `{entity, related, relationships: {incoming, outgoing}, related_names, status}`. |
| `GET /api/knowledge/context` | `tool` and/or `category` | Relevant `entities`, plus grouped `principles` and `habits`. |

Supported context categories are `people`, `strategy`, `execution`, and `cash`.
Category membership is inferred from name, description and keyword signals; it
is not stored as a dedicated Entity field.

## Generation and Change Rules

Regenerate the artifact from the repository root with:

```bash
python3 escala_server/data/book_parser.py
```

After any schema or curated-data change:

1. Regenerate `book-knowledge.json`.
2. Run `tests/test_book_parser.py`, `tests/test_knowledge_ingester.py`, and
   `tests/test_knowledge_api.py`.
3. Run the complete suite before commit.
4. Treat changes to required fields, enums, edge direction, or ID semantics as
   breaking changes.

Before a breaking change, add an explicit `schema_version` to `meta` and a
migration strategy. Recommended future hardening includes persisting the JSON
Entity `id`, relationship provenance, foreign keys, and database uniqueness.
