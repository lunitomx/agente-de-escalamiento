#!/usr/bin/env python3
"""
Book Parser for Scaling Up by Verne Harnish.
Reads scaling_up_llamaparse.md and extracts:
  - Chapter/section tree from markdown headings
  - Entities: concepts, tools, metrics, habits, principles
  - Relationships between entities
Outputs to escala_server/data/book-knowledge.json
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_FILE = PROJECT_ROOT / "scaling_up_llamaparse.md"
OUTPUT_FILE = Path(__file__).resolve().parent / "book-knowledge.json"

# ── Entity Database ──────────────────────────────────────────────────────────
# Curated from the context task description and book structure.
# Each entry: (id, name, type, description, keywords)

ENTITIES = [
    # ── Concepts ─────────────────────────────────────────────────────────
    ("power-of-one", "Power of One", "concept",
     "The 7 main financial levers that affect cash flow. A 1% or one-day change to each lever compounds to dramatically improve operating cash flow.",
     ["7 levers", "cash flow", "financial levers", "one percent"]),
    ("cash-conversion-cycle", "Cash Conversion Cycle (CCC)", "concept",
     "The time it takes to convert investments in inventory and other resources into cash flows from sales. Measures AR Days + Inventory Days - AP Days.",
     ["CCC", "cash cycle", "working capital", "AR days", "inventory days", "AP days"]),
    ("rockefeller-habits", "Rockefeller Habits", "concept",
     "A set of 10 foundational habits for scaling a business, including daily huddle, weekly meeting rhythms, priorities, data, and scoreboards.",
     ["10 habits", "routines", "disciplines", "mastering"]),
    ("4d-framework", "4D Framework", "concept",
     "The Gazelles framework organized around the 4 Decisions every leader must address: People, Strategy, Execution, and Cash.",
     ["four decisions", "people strategy execution cash", "growth framework"]),
    ("brand-promise", "Brand Promise", "concept",
     "The 3 key promises a company makes to its core customers that differentiate it from competitors (e.g., Southwest: Low Fares, Lots of Flights, Lots of Fun).",
     ["brand promises", "differentiation", "kept promise indicators"]),
    ("bhag", "Big Hairy Audacious Goal (BHAG)", "concept",
     "A 10-to-25-year aspirational goal that provides constant context for all decisions throughout the organization. Concept from Jim Collins.",
     ["10-25 year goal", "summit", "collins", "audacious"]),
    ("one-page-strategic-plan", "One-Page Strategic Plan (OPSP)", "concept",
     "The best-known Gazelles tool driving alignment, accountability, and focus. 7 columns answering Who, What, When, Where, How, Why, Should/Shouldn't.",
     ["OPSP", "strategic plan", "one page", "7 columns"]),
    ("profit-per-x", "Profit per X", "concept",
     "The key economic driver / fundamental metric that determines profitability per unit of the critical constraint (e.g., profit per customer, profit per employee).",
     ["economic driver", "fundamental metric", "per unit"]),
    ("core-customers", "Core Customers", "concept",
     "The specific customer segment the company serves best, for whom the 3 Brand Promises are designed and kept.",
     ["target market", "customer segment", "ideal customer"]),
    ("core-values", "Core Values", "concept",
     "The handful of rules defining the company culture, reinforced through People (HR) systems on a daily basis.",
     ["rules", "culture", "values", "behavior"]),
    ("core-purpose", "Core Purpose", "concept",
     "The deeper 'why' behind the company's existence — what difference it makes in the world. A better word for 'mission.'",
     ["why", "mission", "difference", "purpose"]),
    ("swt", "SWT (Strengths, Weaknesses, Trends)", "concept",
     "An augmented SWOT that explores broader external trends beyond one's own industry. Prevents inside/industry myopia.",
     ["SWOT", "trends", "external", "myopia"]),
    ("7-strata-of-strategy", "7 Strata of Strategy", "concept",
     "Seven components of a robust strategy: words, sandbox, brand promises, KPIs, X-factor, profit-per-X, BHAG.",
     ["seven strata", "stratum", "industry dominating", "differentiation"]),
    ("topgrading", "Topgrading", "concept",
     "A hiring methodology for interviewing and selecting A-player talent, using structured scorecards and deep reference checks.",
     ["hiring", "a-player", "brad smart", "interviewing"]),
    ("lean", "Lean", "concept",
     "Management practice invented by Toyota focused on streamlining and speeding up processes, eliminating waste.",
     ["toyota", "process improvement", "waste elimination", "streamline"]),

    # ── Tools ────────────────────────────────────────────────────────────
    ("face", "FACe (Function Accountability Chart)", "tool",
     "Lists the key functions (seats) all organizations must fill, with person accountable, leading KPIs, and outcomes. Gets the right butts in the right seats.",
     ["function accountability", "seats", "butts in seats", "org chart"]),
    ("pace", "PACe (Process Accountability Chart)", "tool",
     "Maps the 4-9 core processes that drive the company, with person accountable, process name, and 3 KPIs (better, faster, cheaper).",
     ["process accountability", "workflow", "horizontal", "cross-functional"]),
    ("oppp", "OPPP (One-Page Personal Plan)", "tool",
     "Mirrors the OPSP for personal life: Relationships, Achievements, Rituals, Wealth — aligning with People, Strategy, Execution, Cash.",
     ["personal plan", "life plan", "faith family friends fitness finance"]),
    ("vision-summary", "Vision Summary", "tool",
     "A simplified one-page OPSP for companies just getting started or those with 50 or fewer employees. Communicates vision easily.",
     ["simplified opsp", "vision", "one pager"]),
    ("topgrading-interview", "Topgrading Interview", "tool",
     "A structured chronological interview covering every role in the candidate's career, with scorecard and thorough reference checks.",
     ["chronological interview", "candidate assessment", "scorecard"]),
    ("www", "WWW (Who, What, When)", "tool",
     "At the end of weekly meetings, summarize Who said they'll do What, When. Drives clarity in communication and accountability.",
     ["who what when", "action items", "accountability"]),

    # ── Metrics ──────────────────────────────────────────────────────────
    ("revenue-per-employee", "Revenue per Employee", "metric",
     "A key productivity metric measuring total revenue divided by number of employees, indicating operational efficiency.",
     ["productivity", "efficiency", "per person"]),
    ("net-promoter-score", "Net Promoter Score (NPS)", "metric",
     "Customer loyalty metric based on how likely customers are to recommend the company. Scored from -100 to +100.",
     ["NPS", "customer loyalty", "recommend", "fred reichheld"]),
    ("ccc-days", "Cash Conversion Cycle Days", "metric",
     "Number of days cash is tied up in the operating cycle: AR Days + Inventory Days - AP Days.",
     ["CCC", "operating cycle", "days"]),
    ("gross-margin", "Gross Margin", "metric",
     "Revenue minus cost of goods sold, expressed as a percentage. A fundamental profitability metric.",
     ["margin", "profitability", "COGS"]),
    ("kpi", "KPI (Key Performance Indicator)", "metric",
     "Quantifiable measures used to evaluate success. Leading indicators for daily/weekly activities driving results.",
     ["key performance", "indicator", "measure", "score"]),

    # ── Habits ───────────────────────────────────────────────────────────
    ("daily-huddle", "Daily Huddle (15 min)", "habit",
     "A 15-minute daily stand-up meeting to align the team, share priorities, and surface issues. Rockefeller Habit cornerstone.",
     ["morning huddle", "stand-up", "daily meeting", "alignment"]),
    ("weekly-meeting", "Weekly Meeting (90 min)", "habit",
     "A 90-minute weekly executive meeting focused on reviewing KPIs, priorities, customer feedback, and one major topic.",
     ["weekly executive", "90 minutes", "review", "cadence"]),
    ("quarterly-planning", "Quarterly Planning (off-site)", "habit",
     "A quarterly off-site planning session to review strategy, set next quarter priorities, and define the quarterly Theme.",
     ["off-site", "quarterly", "planning", "theme", "90 days"]),
    ("annual-plan", "Annual Plan", "habit",
     "Annual strategic planning to set yearly goals, review progress toward BHAG, and align resources.",
     ["yearly planning", "annual strategy", "goals"]),
    ("monthly-meeting", "Monthly Meeting", "habit",
     "Monthly learning session to review trends, share best practices, and develop the team.",
     ["monthly review", "learning", "development"]),

    # ── Principles ───────────────────────────────────────────────────────
    ("no-surprises", "No Surprises", "principle",
     "Bad news early is good news. Create a culture where issues surface quickly so they can be addressed before becoming crises.",
     ["bad news early", "transparency", "communication"]),
    ("keep-things-simple", "Keep Things Simple", "principle",
     "Everything should be made as simple as possible, but not simpler (Einstein). Complexity is the enemy of execution.",
     ["simple", "einstein", "complexity", "simplicity"]),
    ("same-page", "Same Page", "principle",
     "Everyone in the organization is aligned around the same vision, priorities, and metrics. Driven by the OPSP.",
     ["alignment", "aligned", "one page", "unified"]),
    ("priority-number-one", "Priority #1", "principle",
     "The single most important thing that must be accomplished this quarter. Finish lines every 90 days.",
     ["number one", "quarterly priority", "finish line", "focus"]),
    ("healthy-conflict", "Healthy Conflict", "principle",
     "Organizations need constructive debate and disagreement to make better decisions. Silence is dangerous.",
     ["debate", "disagreement", "constructive", "Pat Lencioni"]),
    ("routine-sets-you-free", "Routine Sets You Free", "principle",
     "Goals without routines are wishes. The right habits and rhythms give freedom to focus on what matters most.",
     ["routine", "habit", "discipline", "freedom"]),
    ("delegate-and-predict", "Delegate and Predict", "principle",
     "Leaders must develop the capability to delegate work and predict outcomes. The fundamental job of a leader is prediction (Deming).",
     ["delegation", "prediction", "deming", "leader role"]),
]

# ── Relationships ────────────────────────────────────────────────────────────
# (source_id, target_id, type, weight, description)

RELATIONSHIPS = [
    # Framework structure
    ("4d-framework", "people-decision", "contains", 1.0, "4D Framework includes the People Decision"),
    ("4d-framework", "strategy-decision", "contains", 1.0, "4D Framework includes the Strategy Decision"),
    ("4d-framework", "execution-decision", "contains", 1.0, "4D Framework includes the Execution Decision"),
    ("4d-framework", "cash-decision", "contains", 1.0, "4D Framework includes the Cash Decision"),

    # People Decision relationships
    ("face", "people-decision", "is_tool_for", 1.0, "FACe is the primary tool for the People Decision"),
    ("pace", "people-decision", "is_tool_for", 1.0, "PACe is a key tool for the People Decision"),
    ("topgrading", "people-decision", "is_tool_for", 1.0, "Topgrading is the hiring methodology for People"),
    ("topgrading-interview", "topgrading", "implements", 1.0, "Topgrading Interview implements Topgrading methodology"),
    ("core-values", "people-decision", "belongs_to", 0.9, "Core Values are reinforced through People systems"),
    ("oppp", "people-decision", "is_tool_for", 0.8, "OPPP supports personal alignment with People Decision"),

    # Strategy Decision relationships
    ("one-page-strategic-plan", "strategy-decision", "is_tool_for", 1.0, "OPSP is the primary tool for the Strategy Decision"),
    ("7-strata-of-strategy", "strategy-decision", "is_tool_for", 1.0, "7 Strata is the strategic thinking framework"),
    ("swt", "strategy-decision", "is_tool_for", 0.9, "SWT feeds into the Strategy Decision"),
    ("vision-summary", "one-page-strategic-plan", "implements", 0.9, "Vision Summary is a simplified OPSP"),
    ("bhag", "strategy-decision", "belongs_to", 1.0, "BHAG is a cornerstone of Strategy"),
    ("core-customers", "strategy-decision", "belongs_to", 1.0, "Core Customers are defined in Strategy"),
    ("brand-promise", "strategy-decision", "belongs_to", 1.0, "Brand Promises are defined in Strategy"),
    ("profit-per-x", "strategy-decision", "belongs_to", 1.0, "Profit per X is the 7th Strata of Strategy"),
    ("core-purpose", "strategy-decision", "belongs_to", 0.9, "Core Purpose is a strategy component"),

    # Execution Decision relationships
    ("rockefeller-habits", "execution-decision", "belongs_to", 1.0, "Rockefeller Habits drive the Execution Decision"),
    ("daily-huddle", "rockefeller-habits", "contained_in", 1.0, "Daily Huddle is a Rockefeller Habit"),
    ("weekly-meeting", "rockefeller-habits", "contained_in", 1.0, "Weekly Meeting is part of the Rockefeller Habits"),
    ("quarterly-planning", "rockefeller-habits", "contained_in", 1.0, "Quarterly Planning is a Rockefeller Habit"),
    ("annual-plan", "rockefeller-habits", "contained_in", 1.0, "Annual Plan is part of the Rockefeller Habits"),
    ("monthly-meeting", "rockefeller-habits", "contained_in", 0.9, "Monthly Meeting is part of the Rockefeller Habits"),
    ("www", "execution-decision", "is_tool_for", 0.9, "WWW drives execution accountability"),
    ("kpi", "execution-decision", "belongs_to", 1.0, "KPIs are key to execution data"),

    # Cash Decision relationships
    ("power-of-one", "cash-decision", "belongs_to", 1.0, "Power of One is a Cash Decision tool"),
    ("cash-conversion-cycle", "cash-decision", "belongs_to", 1.0, "CCC is a core Cash concept"),
    ("ccc-days", "cash-conversion-cycle", "measures", 1.0, "CCC Days measures the Cash Conversion Cycle"),
    ("revenue-per-employee", "cash-decision", "relates_to", 0.7, "Revenue per Employee impacts cash efficiency"),
    ("gross-margin", "cash-decision", "relates_to", 0.8, "Gross Margin drives cash generation"),

    # Principles → framework relationships
    ("no-surprises", "execution-decision", "applies_to", 1.0, "No Surprises principle drives transparent execution"),
    ("keep-things-simple", "4d-framework", "applies_to", 1.0, "Keep Things Simple guides the 4D Framework design"),
    ("same-page", "strategy-decision", "applies_to", 1.0, "Same Page principle underpins the OPSP"),
    ("priority-number-one", "execution-decision", "applies_to", 1.0, "Priority #1 drives execution focus"),
    ("healthy-conflict", "people-decision", "applies_to", 0.9, "Healthy Conflict enables better People decisions"),
    ("routine-sets-you-free", "execution-decision", "applies_to", 1.0, "Routine Sets You Free is the foundation of Rockefeller Habits"),
    ("delegate-and-predict", "people-decision", "applies_to", 1.0, "Delegate and Predict defines leadership capability"),

    # Tool → tool relationships
    ("face", "pace", "complements", 1.0, "FACe (vertical functions) complements PACe (horizontal processes)"),
    ("one-page-strategic-plan", "7-strata-of-strategy", "incorporates", 1.0, "OPSP incorporates 7 Strata strategic thinking"),
    ("one-page-strategic-plan", "swt", "incorporates", 0.9, "OPSP incorporates SWT analysis"),
    ("oppp", "one-page-strategic-plan", "mirrors", 1.0, "OPPP mirrors the OPSP structure for personal life"),

    # Entity → entity key relationships
    ("power-of-one", "cash-conversion-cycle", "impacts", 1.0, "Power of One levers directly impact the CCC"),
    ("revenue-per-employee", "kpi", "is_a", 1.0, "Revenue per Employee is a KPI"),
    ("net-promoter-score", "kpi", "is_a", 1.0, "Net Promoter Score is a KPI"),
    ("ccc-days", "kpi", "is_a", 1.0, "CCC Days is a KPI"),
    ("gross-margin", "kpi", "is_a", 1.0, "Gross Margin is a KPI"),
    ("profit-per-x", "kpi", "is_a", 0.9, "Profit per X is a critical KPI"),
    ("brand-promise", "core-customers", "serves", 1.0, "Brand Promises serve Core Customers"),
    ("lean", "pace", "improves", 0.8, "Lean principles improve process flows in PACe"),

    # Cross-decision relationships
    ("rockefeller-habits", "strategy-decision", "supports", 0.8, "Rockefeller Habits enable strategy execution"),
    ("one-page-strategic-plan", "execution-decision", "enables", 0.9, "OPSP drives execution alignment"),
    ("cash-conversion-cycle", "strategy-decision", "informs", 0.7, "CCC understanding informs strategic choices"),
    ("power-of-one", "execution-decision", "informs", 0.7, "Power of One analysis informs execution priorities"),
    ("core-values", "topgrading", "guides", 0.8, "Core Values guide Topgrading hiring decisions"),
    ("weekly-meeting", "same-page", "reinforces", 0.9, "Weekly meeting rhythm reinforces Same Page alignment"),
    ("daily-huddle", "priority-number-one", "reinforces", 0.9, "Daily Huddle reinforces Priority #1 focus"),
    ("kpi", "no-surprises", "enables", 0.8, "KPIs enable No Surprises by surfacing issues early"),
]


def _make_decision_chapters(chapters: list[dict]) -> list[dict]:
    """Create the 4 decision nodes: People, Strategy, Execution, Cash."""
    decisions = [
        {"id": "people-decision", "name": "People", "type": "decision",
         "description": "The decision about attracting, keeping, and growing the right people.",
         "keywords": ["people", "team", "leaders", "managers", "talent"],
         "line_refs": [1110, 1118, 1395, 1476, 1619, 1972, 2278]},
        {"id": "strategy-decision", "name": "Strategy", "type": "decision",
         "description": "The decision about crafting a truly differentiated strategy that matters to customers.",
         "keywords": ["strategy", "core", "BHAG", "7 strata", "OPSP"],
         "line_refs": [2605, 2619, 2672, 2872, 3112, 3512, 3944]},
        {"id": "execution-decision", "name": "Execution", "type": "decision",
         "description": "The decision about driving flawless execution through priorities, data, and meeting rhythm.",
         "keywords": ["execution", "priority", "data", "meeting rhythm", "habits"],
         "line_refs": [4498, 4510, 4746, 5076, 5478]},
        {"id": "cash-decision", "name": "Cash", "type": "decision",
         "description": "The decision about managing cash flow to weather storms and fuel growth.",
         "keywords": ["cash", "accounting", "power of one", "CCC", "cash flow"],
         "line_refs": [5916, 5928, 5960, 6241, 6456, 6952]},
    ]
    for d in decisions:
        d["chapter_ids"] = _find_chapter_ids(chapters, d["line_refs"])
    return decisions


def parse_chapters(text: str) -> list[dict]:
    """Extract chapter/section tree from markdown headings."""
    lines = text.split("\n")
    headings = []

    for i, line in enumerate(lines, start=1):
        match = re.match(r"^(#{1,3})\s+(.+?)(?:\s*\{[^}]*\})?$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            # Skip image/table lines masquerading as headings
            if title.startswith("![") or title.startswith("<"):
                continue
            headings.append({"level": level, "title": title, "line": i})

    # Build tree
    def build_tree(hlist: list, parent_level: int = 0, start_idx: int = 0) -> tuple[list, int]:
        result = []
        idx = start_idx
        while idx < len(hlist):
            h = hlist[idx]
            if h["level"] <= parent_level:
                break
            chapter_id = _make_slug(h["title"])
            children = []
            peek = idx + 1
            if peek < len(hlist) and hlist[peek]["level"] > h["level"]:
                children, consumed = build_tree(hlist, h["level"], peek)
                idx = consumed
            else:
                idx += 1

            # Find line end: start of next heading at same or higher level, or EOF
            line_end = len(lines)
            for h2 in hlist:
                if h2["line"] > h["line"] and h2["level"] <= h["level"]:
                    line_end = h2["line"] - 1
                    break

            result.append({
                "id": idx,
                "title": h["title"],
                "level": h["level"],
                "line_start": h["line"],
                "line_end": line_end,
                "slug": chapter_id,
                "children": children,
            })
        return result, idx

    tree, _ = build_tree(headings)
    return _flatten_and_number(tree)


def _flatten_and_number(tree: list[dict]) -> list[dict]:
    """Assign sequential IDs and flatten children into chapters list."""
    result = []
    counter = [0]

    def walk(nodes, parent_id=None):
        for n in nodes:
            counter[0] += 1
            n["id"] = counter[0]
            if parent_id is not None:
                n["parent_id"] = parent_id
            children = n.pop("children", [])
            result.append(n)
            walk(children, n["id"])

    walk(tree)
    return result


def _make_slug(title: str) -> str:
    """Create a URL-friendly slug from a title."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"\s+", "-", slug)
    return slug.strip("-")


def _find_line_refs(text: str, keywords: list[str], max_refs: int = 20) -> list[int]:
    """Find line numbers where any keyword appears (case-insensitive)."""
    lines = text.split("\n")
    refs = set()
    for pattern in keywords:
        escaped = re.escape(pattern)
        for i, line in enumerate(lines, start=1):
            if re.search(escaped, line, re.IGNORECASE):
                refs.add(i)
                if len(refs) >= max_refs:
                    break
        if len(refs) >= max_refs:
            break
    return sorted(refs)[:max_refs]


def _find_chapter_ids(chapters: list[dict], line_refs: list[int]) -> list[int]:
    """Map line refs to the chapters they belong to."""
    chapter_ids = set()
    for ref in line_refs:
        for ch in chapters:
            if ch["line_start"] <= ref <= ch["line_end"]:
                chapter_ids.add(ch["id"])
    return sorted(chapter_ids)


def extract_entities(text: str, chapters: list[dict]) -> list[dict]:
    """Build entity list with line refs found in the text."""
    entities = []
    for eid, name, etype, description, keywords in ENTITIES:
        line_refs = _find_line_refs(text, [name] + keywords)
        chapter_ids = _find_chapter_ids(chapters, line_refs)
        entities.append({
            "id": eid,
            "name": name,
            "type": etype,
            "description": description,
            "keywords": keywords,
            "line_refs": line_refs,
            "chapter_ids": chapter_ids,
        })
    return entities


def extract_relationships(text: str) -> list[dict]:
    """Build relationships list, finding line refs in text."""
    rels = []
    for source_id, target_id, rtype, weight, description in RELATIONSHIPS:
        # Find line refs for the source entity
        line_refs = _find_line_refs(text, [source_id.replace("-", " ")], max_refs=1)
        rels.append({
            "source": source_id,
            "target": target_id,
            "type": rtype,
            "weight": weight,
            "line_ref": line_refs[0] if line_refs else None,
            "description": description,
        })
    return rels


def parse_book() -> dict:
    """Main parse function. Returns the complete book-knowledge dict."""
    print(f"Reading {SOURCE_FILE}...")
    text = SOURCE_FILE.read_text(encoding="utf-8")

    print("Parsing chapters...")
    chapters = parse_chapters(text)

    print("Extracting entities...")
    entities = extract_entities(text, chapters)
    # Add decision entities
    entities.extend(_make_decision_chapters(chapters))

    print("Extracting relationships...")
    relationships = extract_relationships(text)

    return {
        "meta": {
            "source": "scaling_up_llamaparse.md",
            "entities_count": len(entities),
            "relationships_count": len(relationships),
        },
        "chapters": chapters,
        "entities": entities,
        "relationships": relationships,
    }


def main():
    result = parse_book()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing {OUTPUT_FILE}...")
    OUTPUT_FILE.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Done! {result['meta']['entities_count']} entities, "
          f"{result['meta']['relationships_count']} relationships, "
          f"{len(result['chapters'])} chapters.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
