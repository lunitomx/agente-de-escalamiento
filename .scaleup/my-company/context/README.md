# Company Context

Structured facts about the company that the agent uses for personalized coaching.

Each file is a YAML document with a specific category:

- `org.yaml` — Organizational structure, roles, team
- `metrics.yaml` — Key financial and operational metrics
- `competitive.yaml` — Competitive landscape, market position
- `custom.yaml` — User-defined facts

The agent reads these files during session start and uses them to personalize recommendations.
