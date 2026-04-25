---
name: scaleup-close-sync
description: 'Ensure session infrastructure exists. Sub-skill of /scaleup-close. STUB — full sync in S7.2.'
---

# Sync Session State (STUB)

## Purpose

Verify that session infrastructure is in place after writing the log. Sub-skill of `/scaleup-close`.

**Note:** This is a stub for S7.1. Full YAML-to-markdown rendering of company profile and state files is deferred to S7.2 (Persistent Memory).

## Steps

### Step 1: Verify Sessions Directory

```bash
ls -la .scaleup/my-company/sessions/ 2>/dev/null
```

Confirm the directory exists and contains the session log just written.

### Step 2: Verify Log File

Confirm the session log file exists and is non-empty.

### Step 3: Report

Report that session data has been saved successfully.

## Output

Confirmation that session log was persisted.
