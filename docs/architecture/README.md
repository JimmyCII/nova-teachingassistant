# Agent Role Prompts — TeacherMind

Multi-agent role set (Project-Playbook §4), tailored to TeacherMind. The orchestrator routes work
to the lowest sufficient cost tier and logs decisions in `../logs/routing-audit-log.md`.

Standard roles (populate as the build begins):

- `00-orchestrator.md` — owns structure, task routing, acceptance criteria, handoff review,
  decision log. Writes little code itself. **(drafted)**
- `01-inspector.md` — gathers source material / existing-system inventory. *(to tailor)*
- `02-product-ux.md` — flows and UX for the teacher's conversational experience. *(to tailor)*
- `03-data-model.md` — schema + core logic (grade data, standards, students). **Must lock before any
  UI.** *(to tailor)*
- `04-frontend.md` — any UI surface (chat client). *(to tailor)*
- `05-backend.md` — ADK tools, Canvas/CSV integrations, data layer. *(to tailor)*
- `06-qa.md` — edge cases, the Major-Cluster rule, PII-safety of test data. *(to tailor)*
- `07-documentation.md` — README, setup, user guide, decisions. *(to tailor)*

> Tailor each from `C:\Users\jimco\Dev\Project-Playbook\templates\agents\` as the corresponding work
> begins (add one specialist at a time and audit for a week per the playbook).
