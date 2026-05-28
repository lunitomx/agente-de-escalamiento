# ADR: Visualization Framework for E14 Cash Dashboards

## Status: Accepted

**Date:** 2026-05-27
**Applies to:** E14 (Cash Dashboards), E15 (Strategy), E16 (People), E17 (Execution) — all 22 visual dashboard stories
**Decision owner:** S14.1 walking skeleton — s14.1-cash-visual

---

## Context

ScaleUp's coaching skills are text-guided. E14 introduces the first visual dashboards across the Cash decision. The framework chosen here becomes the standard for all 22 subsequent visual stories. Constraints from the project:

1. **No build step** — ScaleUp is local-first (clone-and-run). No npm, webpack, or bundler required.
2. **Claude Code preview compatible** — Dashboards must render in Claude Code's built-in HTML preview.
3. **Single-file components** — Each dashboard is a self-contained `.html` file; no server required.
4. **Reusability** — S14.2 needs bar/comparison charts, S14.4 needs a radar chart. The framework must support all chart types needed across E14–E17.
5. **Zero cost, no auth** — No paid API or CDN authentication.

---

## Options Considered

### Option A: Pure HTML/CSS/JS (no library)

**Pros:** Zero dependencies, truly offline, fully self-contained.
**Cons:** Implementing radar charts (S14.4) and bar comparisons (S14.2) manually is disproportionate effort. SVG math for radar requires significant custom code that will drift and break.

**Verdict: Rejected.** Adequate for S14.1 but creates rework debt at S14.4.

### Option B: React + Recharts

**Pros:** Excellent component model, rich chart types, great ecosystem.
**Cons:** Requires npm install, build step, and dev server. Violates the no-build constraint. Cannot be previewed directly as a standalone HTML file.

**Verdict: Rejected.** Hard constraint violation.

### Option C (Selected): Vanilla HTML/CSS/JS + Chart.js (vendored locally)

**Pros:**
- Zero build step — script tag only
- Chart.js supports bar, line, doughnut, radar, and mixed charts — covers all E14–E17 needs
- Self-contained when vendored (offline-capable, no CDN dependency at runtime)
- Claude Code preview compatible (HTML file opens directly)
- Tiny authoring footprint: one `<script>` tag per dashboard
- Chart.js is battle-tested (v4.x) with excellent radar support for S14.4

**Cons:**
- Requires vendoring `chart.min.js` locally (~60 KB minified gzip) under `components/shared/vendor/`
- No reactive binding — JavaScript must imperatively update chart data; acceptable for read-only dashboards

**Verdict: Selected.**

---

## Decision (D1): Vanilla HTML/CSS/JS + Chart.js v4 (vendored)

```
components/
  shared/
    vendor/
      chart.umd.min.js       ← Chart.js v4.x, vendored (downloaded once)
      chartjs-chart-matrix.js ← optional plugin for heatmap in future stories
    styles/
      dashboard-base.css      ← shared grid, semáforo, typography tokens
  cash-board/
    index.html               ← S14.1 CASh dashboard (self-contained)
  power-of-one/
    index.html               ← S14.2
  fundability/
    index.html               ← S14.4
  recurring-revenue/
    index.html               ← S14.3
```

**Self-contained definition:** Each `index.html` uses a relative `<script>` tag to load from `../shared/vendor/chart.umd.min.js`. No internet connection needed after the vendor file is downloaded once. This satisfies AC6 ("no external API calls").

**Alternative if offline-vendoring is impractical for this story:** Use Chart.js via jsDelivr CDN (`https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js`). Clearly documented as a "CDN mode" fallback. Implementation note will flag this as a `TODO: vendor locally`.

---

## Impact on Future Stories

| Story | Chart type needed | Chart.js support |
|-------|-------------------|-----------------|
| S14.1 — CASh Board | Bar (progress meter per ciclo), CSS semáforo | Native bar chart + CSS |
| S14.2 — Power of One | Horizontal bar (current vs adjusted, 7 vars) | Native horizontal bar |
| S14.4 — Fundability | Radar (8 criteria) | Native radar |
| S14.3 — Recurring Revenue | Hierarchy + badge grid (no chart needed) | CSS-only, Chart.js optional |
| E15–E17 | Scorecard grids, bar charts, gauge-style progress | Native bar + doughnut |

All types confirmed supported without additional libraries.

---

## Consequences

- All dashboard HTML files MUST reference `../shared/vendor/chart.umd.min.js` via relative path
- `dashboard-base.css` must be created in S14.1 and reused (not duplicated) by all stories
- Semantic color tokens (--color-green, --color-yellow, --color-red) must be defined once in `dashboard-base.css`
- Any story that introduces a new Chart.js plugin must add it to `shared/vendor/` and document in this ADR
