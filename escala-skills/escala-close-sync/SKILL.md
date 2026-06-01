---
name: escala-close-sync
description: 'Sync YAML to markdown views on session close. Sub-skill of /escala-close.'
---

# Sync State to Markdown Views

## Purpose

Generate human-readable markdown files from YAML source of truth. Sub-skill of `/escala-close`.

## Steps

### Step 1: Render Company Profile

Run the Python renderer:

```bash
python3 -c "
import sys, pathlib
sys.path.insert(0, str(pathlib.Path('.escala/agent')))
from validators.memory import render_profile_markdown
md = render_profile_markdown(pathlib.Path('.escala/agent/memory/company-profile.yaml'))
pathlib.Path('.escala/my-company/profile.md').write_text(md)
print('Profile rendered')
"
```

This overwrites `.escala/my-company/profile.md` with a clean render from the YAML.

### Step 2: Verify Files

Confirm that the following files exist and are non-empty:
- `.escala/my-company/profile.md` — rendered from YAML
- `.escala/my-company/sessions/` — contains at least today's session log

### Step 3: Report

Report which files were synced.

## Output

| Item | Destination |
|------|-------------|
| Company profile markdown | `.escala/my-company/profile.md` |
| Verification | Files exist and are non-empty |
