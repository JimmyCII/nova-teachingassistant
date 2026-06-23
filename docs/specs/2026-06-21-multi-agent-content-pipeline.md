# Design — Multi-Agent Content Pipeline (where the agents actually live)

**Date:** 2026-06-21 · **Status:** design for review · **Author:** Jim + Nova
**Refines:** `2026-06-21-adk-orchestrator.md` (changes the specialist roster). **Demonstrates:**
multi-agent ADK as *collaboration on one artifact*, not just request routing.

## The reframe

The earlier orchestrator spec routed to **Homework / DOK / Progress** specialists. Routing alone is
the weakest multi-agent pattern — a switchboard. The real value (and the stronger demo) is **inside**
content creation: homework, quizzes, and group projects should each flow through a **pipeline of
agents that collaborate on the same artifact** — one drafts, one checks it's pedagogically strong,
one makes it fun, and a loop learns what worked so the next one is better.

This also fixes a current weakness: `weekly_quiz.py` and `group_activities.py` are **single
one-shot Gemini calls** today — no standards check, no answer-key verification, no tests. A reviewer
agent in the pipeline turns those into trustworthy materials.

## The pipeline (every content type runs through it)

```
Karrie ─▶ Nova (orchestrator / thought partner)
              │  clarifies, picks type, logs request
              ▼
        ┌───────────────┐   draft
        │ GENERATOR      │ ─────────────┐
        │ (homework /    │              ▼
        │  quiz / group) │       ┌──────────────────┐ revise  ┌───────────────┐
        └───────────────┘       │ PEDAGOGY CRITIC   │◀───────▶│  (loop back to │
                                │ "strong content"  │         │   generator)   │
                                └──────────────────┘         └───────────────┘
                                         │ approved-for-rigor
                                         ▼
                                ┌──────────────────┐
                                │ ENRICHMENT / VISUAL│  figures + fun
                                └──────────────────┘
                                         ▼
                                draft saved to Drive (02_Generated) ─▶ Karrie reviews
                                         │
                                         ▼
                       ┌──────────────────────────────┐
                       │ PERFORMANCE / INSIGHT agent   │ ◀── approvals, edits, mastery
                       │ "increase performance"        │ ──▶ what to make next + how to make it better
                       └──────────────────────────────┘
```

## The agents

**Nova — root orchestrator / thought partner.** Talks to Karrie, asks one clarifying question,
selects the content type, runs the pipeline, returns the result, logs it (`request_logger`).

**Tier 1 — Generators (the "what to make").** Already exist: spiral homework (`.xlsx`, mature),
weekly quiz, DOK group activity. They produce a first draft in a common internal shape.

**Tier 2 — Shared reviewers (run on EVERY artifact):**
- **Pedagogy/Standards Critic — "strong content."** Verifies: AZ standard alignment, DOK-level
  accuracy (Webb verb cues), 6th-grade rigor + reading level, **answer-key correctness**, and
  PII-safety (fictional names only). Returns fixes to the generator (a generate→critique→revise
  loop, bounded retries). This is the single highest-leverage agent — it makes the one-shot quiz/DOK
  tools trustworthy *and* is the clearest multi-agent demo.
- **Enrichment/Visual — "add fun."** Adds the decorative/seasonal layer (Brain Break, themed header
  art) and requests the **math figures** a problem needs. Two very different jobs, two solutions —
  see §Images.

**Tier 3 — Improvement loop (the "increase performance," two readings):**
- **Performance/Insight agent.** (a) *Students:* reads the anonymous mastery store + request log →
  recommends what to generate next and at what DOK level (target the gaps). (b) *Nova herself:*
  learns from what Karrie **approves vs. edits vs. rejects** (the `03_Approved` folder + request-log
  status) → feeds style/quality signals back into the generators and the critic, so Nova gets better
  at being *Karrie's* assistant over time. This is the eval/feedback loop the course emphasizes.

## Images — two needs, two solutions (don't conflate)

1. **Math figures** (number line, coordinate plane, net, bar model) must be **correct** → render
   **deterministically** (matplotlib/SVG), never an image model. Owned by Enrichment, *checked by the
   Critic*. (The homework spec already uses labeled `[figure: …]` placeholders — this fills them.)
2. **Decorative "fun"** (seasonal art, doodles, theme headers) must be **safe + licensed** →
   the Enrichment agent **generates original art with Imagen/Gemini** (CONFIRMED 2026-06-21:
   generate, don't fetch). **Personalized to Karrie** (CONFIRMED): the agent themes the art from
   either (a) **Karrie's explicit input** ("make it autumn / pumpkins / basketball season"), or
   (b) **what Nova knows about Karrie** — her palette (Deep Plum `#3A1F4B` → Milestone Gold
   `#DDA440`), the current season/month, and the real-world contexts she favors. So the worksheet
   art feels like *hers*.
   **Guardrails (non-negotiable):** original generation only — **never** scrape web images; and
   **no copyrighted characters** in student-facing materials. Karrie's Star Wars/Disney fandom flavors
   *Nova's persona and the chat*, **not** the worksheets (use *motifs* — "space adventure," "castle"
   — not Vader/Mickey). The Pedagogy Critic also screens generated art for appropriateness.

## How it maps to existing decisions

- **Still ADK `sub_agents` (primary) + flat-tool fallback** (per the orchestrator spec). Critic and
  Enrichment are **pipeline stages the orchestrator invokes in sequence** (sub-agents called in order,
  or `AgentTool`s the generator calls).
- **Standardize quiz + DOK onto the homework pattern** (split "thinking" from "drawing," validated
  spec) so the Critic has a structured artifact to check and the output can be `.xlsx` (per the
  locked DOK decision), not raw Markdown.
- **The Drive/Curriculum MCP is the feedback substrate** — `02_Generated`, `03_Approved`, the request
  log, and the mastery store are how the Performance agent observes "what worked."

## Recommended build order (within Session 7, the orchestrator)

1. **Pedagogy/Standards Critic first.** Biggest quality lift, pure-text, lowest risk; wraps the
   existing generators with a review pass and instantly upgrades the untested quiz/DOK tools. **This
   alone demonstrates multi-agent collaboration** for the capstone.
2. **Enrichment — figures first (deterministic), decorative art second (Imagen).**
3. **Performance/Insight agent** once the mastery store (Session 4) + approved-folder signal exist.

## Course-concept payoff
A generate→critique→enrich pipeline is genuine multi-agent ADK (collaboration + a reflection/critic
loop), not routing — exactly what the judges look for, and it makes every piece of content Karrie
gets demonstrably stronger.

## Decisions (resolved 2026-06-21)
- **Decorative images: Imagen generation, personalized to Karrie** (her input or her known
  profile/palette/season). Math figures stay deterministic. Guardrails above (original-only, no
  copyrighted characters; Critic screens). A licensed-stock MCP is a possible *later* add, not v1.
