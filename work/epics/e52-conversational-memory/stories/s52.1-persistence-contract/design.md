# S52.1 Persistence Contract

## Storage

- **Path**: `.escala/agent/memory/welcome-state.yaml`
- **Format**: YAML, human-readable
- **Scope**: Per-company workspace (isolated by `base_path`)

## Persisted Fields

From `WelcomeState`:
- `phase`: current conversation phase
- `profile`: maturity profile (explorer, specific, directed, returning)
- `returning`: whether this is a returning user flow
- `previous_focus`: last decision focus, if returning
- `concern`: user's stated concern
- `area`: detected decision area (people, strategy, execution, cash)
- `next_action`: internal next action

Additional metadata:
- `authorized_at`: ISO timestamp of explicit user authorization
- `updated_at`: ISO timestamp of last write
- `schema_version`: `1`

## Authorization Rule

State is written only when the user explicitly authorizes persistence.
Example prompts:
- "¿Guardo esta conversación para continuar la próxima vez?"
- If user answers yes → set `authorized_at` and write.
- If user answers no → do not write; delete any existing state if requested.

## Freshness / Invalidation

- State older than 7 days is considered stale.
- On stale state, the agent presents a summary and asks the user to confirm or restart.
- State is invalidated when the user completes onboarding or explicitly asks to restart.

## Privacy

- Stored only in the local workspace.
- Never synced to cloud or shared across companies.
- No raw user messages are stored verbatim.

## API for S52.2

```python
def save_welcome_state(
    base_path: Path, state: WelcomeState, authorized: bool
) -> Path | None: ...
def load_welcome_state(base_path: Path) -> WelcomeState | None: ...
def is_state_fresh(state: WelcomeState, max_age_days: int = 7) -> bool: ...
```
