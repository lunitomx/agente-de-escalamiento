# ScaleUp Ontology Schema

## Overview

The ScaleUp knowledge base is a structured domain ontology — a graph of nodes and relationships that represents the Scaling Up methodology. Each node is a YAML file. Relationships are declared as adjacency lists within each node.

## Node Types

| Type | Description | Example |
|------|-------------|---------|
| `decision` | The 4 core decisions | People, Strategy, Execution, Cash |
| `concept` | Principles and frameworks | "Right people right seats", "One thing" |
| `tool` | Actionable frameworks/checklists | FACe/PACe, 7 Strata, Rockefeller Habits |
| `worksheet` | Completable templates with fields | OPSP, CCC worksheet, OPPP |
| `stage` | Business maturity stages | Startup, Growth, Scaling, Expansion |
| `metric` | Measurable KPIs | CCC days, NPS, Employee turnover |

## Relationship Types

| Type | Direction | Description |
|------|-----------|-------------|
| `belongs-to` | any → decision | Node belongs to a decision area |
| `requires` | any → any | Prerequisite — do A before B |
| `feeds-into` | any → any | Output of A is input to B |
| `measured-by` | concept/tool → metric | How success is measured |
| `prerequisite-of` | any → any | Inverse of requires |
| `implements` | worksheet → concept | Worksheet makes concept actionable |

## Node File Format

Every node is a YAML file with these fields:

### Required Fields (all types)

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique slug (e.g., `tool-opsp`) |
| `type` | enum | One of the 6 node types |
| `name` | string | English name |
| `name_es` | string | Spanish name |
| `decision` | enum | `people`, `strategy`, `execution`, `cash`, or `cross` |
| `summary` | string | 1-3 sentence description |
| `relationships` | list | Adjacency list of `{type, target}` pairs |

### Optional Fields (all types)

| Field | Type | Description |
|-------|------|-------------|
| `source` | object | `{book_chapter, book_line, workbook}` — pointer to LlamaParse content |
| `tags` | list | Keywords for search |
| `metadata` | object | Type-specific metadata |

### Type-Specific Metadata

| Type | Metadata Fields |
|------|----------------|
| `worksheet` | `fields` (list of completable fields), `output` (what it produces) |
| `tool` | `difficulty`, `time_estimate`, `frequency` |
| `metric` | `unit`, `direction` (higher_better / lower_better), `benchmark` |
| `stage` | `revenue_range`, `employee_range`, `characteristics` |

## Directory Structure

```
.scaleup/knowledge/
├── ontology/
│   ├── schema.md              # This file
│   └── node-types.yaml        # Formal type definitions
├── decisions/
│   ├── people.yaml
│   ├── strategy.yaml
│   ├── execution.yaml
│   └── cash.yaml
├── people/
│   ├── tools/
│   ├── concepts/
│   ├── worksheets/
│   └── metrics/
├── strategy/
│   ├── tools/
│   ├── concepts/
│   ├── worksheets/
│   └── metrics/
├── execution/
│   ├── tools/
│   ├── concepts/
│   ├── worksheets/
│   └── metrics/
├── cash/
│   ├── tools/
│   ├── concepts/
│   ├── worksheets/
│   └── metrics/
└── stages/
```

## Design Principles

1. **One node = one file** — inspectable, editable, diffable
2. **Adjacency list** — relationships declared in each node, not in a separate file
3. **Source pointers** — every node traces back to LlamaParse content (chapter + line)
4. **Bilingual** — name + name_es for all nodes
5. **No embeddings** — deterministic retrieval via symbolic traversal
