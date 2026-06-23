# Routing Audit Log

Tracks how the orchestrator delegated work across Low / Medium / High cost tiers
(Project-Playbook §4). Append one row per routing decision; keep `Task Summary` short and
non-sensitive (no student PII).

## Routing Entries

| Date | Task Summary | Routed To | Risk Level | Escalated | Reason | Confidence |
|------|--------------|-----------|------------|-----------|--------|------------|
| 2026-06-20 | Map W:\ archive (File Cartographer) | Medium (Sonnet) | Low | no | High-volume listing/metadata | High |
| 2026-06-20 | Lesson / Standards / Voice / Scope analysis (4 agents) | Medium (Sonnet) | Medium | no | Document analysis, parallelizable | High |
| 2026-06-20 | Nova self-naming + persona synthesis | High (Opus) | Medium | no | Creative/voice quality matters | High |

## Rules
- `Routed To`: Low / Medium / High (or specific agent). `Risk` & `Confidence`: Low / Medium / High.
- `Escalated`: `yes` if the task moved up a tier mid-request, else `no`.
- Default to the lowest sufficient tier; reserve High for genuinely high-impact work. Review
  periodically and tune routing rules.
