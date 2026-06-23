# Capstone Project Specification
## TeacherMind: An AI Concierge Agent for K-8 Mathematics Teachers

**Track:** Concierge Agents  
**Kaggle Submission Deadline:** July 6, 2026  
**Author:** Jim Cockerham  
**Course:** 5-Day AI Agents: Intensive Vibe Coding Course with Google

---

## 1. Problem Statement

A 6th-grade Arizona mathematics teacher manages 100+ students across multiple class periods, tracking grades, monitoring learning progress against state standards, planning differentiated lessons, and communicating with families — all while preparing and delivering daily instruction. The administrative burden of this work consumes time that could be spent on teaching.

The teacher uses three disconnected systems:
- **Synergy** (Edupoint) — student information system and gradebook
- **Canvas** — LMS for curriculum, assignments, and modules
- **School-Net** — parent/guardian communication platform

None of these systems talk to each other. The teacher manually reconciles data across all three, identifies struggling students by memory, and drafts parent communications from scratch.

**TeacherMind** is an AI concierge agent that unifies these data sources, provides proactive insights aligned to Arizona Mathematics Standards, and handles the drafting work — so the teacher can focus on students.

---

## 2. Solution Overview

TeacherMind is a conversational AI agent powered by Google Gemini, built with the Agent Development Kit (ADK). It gives the teacher a natural-language interface to her student data, curriculum, and communication tools.

### Core Capabilities

| Capability | What it does |
|---|---|
| **Grade Trend Analysis** | Reads Synergy CSV exports, surfaces students falling behind, identifies standard-level weaknesses |
| **Standards Mapping** | Tags every assignment and grade to AZ Math Standard codes (6.RP, 6.NS, 6.EE, 6.G, 6.SP) |
| **Canvas Integration** | Pulls upcoming assignments, module structure, and due dates from Canvas API |
| **At-Risk Flagging** | Proactively flags students at risk in Major Cluster standards (70% of AZ Math instruction time) |
| **Communication Drafting** | Generates School-Net-ready parent messages tailored to each student's situation |
| **Lesson Planning Support** | Suggests instructional focus based on class-wide standard gaps |
| **Guided Notes Tracker** | Maps teacher's guided notes to specific standard codes to track curriculum coverage |

### Sample Interaction

```
Teacher: "Who's struggling in Period 2 and what do I need to address first?"

TeacherMind: "In Period 2, 4 students are below 70% on 6.NS (Number System) 
assignments over the last 3 weeks: Marcus, Aisha, Derek, and Priya. 
6.NS is a Major Cluster — it feeds directly into 7th grade proportional reasoning.

Marcus and Derek are both struggling specifically with fraction division (6.NS.A.1). 
Aisha and Priya are falling behind on multi-digit decimal operations (6.NS.B.3).

Want me to draft a parent note for any of these students, or pull their 
Canvas assignment history to see where things went sideways?"
```

---

## 3. Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    TeacherMind Agent                     │
│              (Gemini + ADK, Google Cloud Run)            │
├──────────────┬──────────────┬──────────────┬────────────┤
│  Grade Tool  │ Canvas Tool  │Standards Tool│ Comms Tool │
│  (Synergy    │  (Canvas     │  (AZ Math    │ (School-Net│
│  CSV reader) │  REST API)   │  Standards)  │  Drafter)  │
└──────┬───────┴──────┬───────┴──────────────┴────────────┘
       │              │
       ▼              ▼
  Google Drive    Canvas API
  (grade exports) (REST v1)
```

### Data Flow

1. Teacher exports grades from Synergy → saves CSV to a designated Google Drive folder
2. Agent reads CSV on demand (or on schedule)
3. Agent pulls Canvas assignments via API
4. Agent maps both to AZ Math Standards
5. Agent answers questions, flags issues, drafts communications

### Technology Stack

| Component | Technology |
|---|---|
| Agent framework | Google ADK (Agent Development Kit) |
| LLM | Gemini 1.5 Pro / Gemini 2.0 Flash |
| Deployment | Google Cloud Run |
| Grade data | Synergy CSV export → Google Drive |
| Curriculum data | Canvas REST API |
| Standards | AZ Math Standards (ADE 2025) embedded as structured data |
| Language | Python 3.11+ |

---

## 4. Arizona Mathematics Standards Alignment

The agent is built around the ADE 6th Grade Math Standards domain structure:

| Domain | Code | Priority | Key Agent Use |
|---|---|---|---|
| Ratios & Proportional Relationships | 6.RP | Major | Track ratio/rate mastery |
| The Number System | 6.NS | Major | Flag fraction/decimal gaps |
| Expressions & Equations | 6.EE | Major | Monitor algebraic thinking |
| Geometry | 6.G | Supporting | Secondary tracking |
| Statistics & Probability | 6.SP | Additional | Data literacy check-ins |

**Rule:** If a student is below threshold on a Major Cluster standard, the agent flags it as Priority 1 regardless of their overall grade.

---

## 5. Data Sources and Access Strategy

### Synergy (Gradebook)
- **Access method:** Manual CSV export by teacher → upload to Google Drive
- **Frequency:** Weekly or after each grading period
- **Fields needed:** Student name, student ID, assignment name, score, max score, date, period/class
- **Agent action:** Reads file, normalizes, maps assignments to standards via name matching + LLM classification

### Canvas (LMS)
- **Access method:** Canvas REST API using teacher's API token
- **Endpoints used:**
  - `GET /api/v1/courses` — list courses
  - `GET /api/v1/courses/:id/assignments` — assignment list with due dates
  - `GET /api/v1/courses/:id/modules` — curriculum modules
  - `GET /api/v1/courses/:id/students` — student roster
- **Agent action:** Pulls upcoming assignments, maps to standards, informs lesson planning

### School-Net (Parent Communication)
- **Access method:** No direct API — agent drafts, teacher sends
- **Agent action:** Generates parent-ready messages with: student name, specific standard(s) of concern, concrete observation, suggested home support, teacher tone/sign-off

### AZ Math Standards
- **Access method:** Embedded in agent as structured JSON
- **Data:** All 6th grade standard codes, descriptions, domain, priority (major/supporting/additional)

---

## 6. Key Agent Tools (Function Signatures)

```python
load_grade_export(filepath: str) -> GradeData
    """Load and normalize a Synergy CSV grade export."""

get_canvas_assignments(course_id: str, days_ahead: int = 14) -> list[Assignment]
    """Fetch upcoming Canvas assignments with due dates."""

map_assignment_to_standard(assignment_name: str, description: str) -> StandardCode
    """Use LLM to map an assignment to the closest AZ Math Standard."""

analyze_grade_trends(grade_data: GradeData, period: str, threshold: float = 0.70)
    """Identify students below threshold, grouped by standard domain."""

get_at_risk_students(grade_data: GradeData, major_only: bool = True) -> list[Student]
    """Return students at risk in Major Cluster standards."""

draft_parent_communication(student: Student, standard: str, context: str) -> str
    """Draft a School-Net-ready parent message."""

get_class_standard_gaps(grade_data: GradeData) -> dict[str, float]
    """Return class-wide average by standard code to identify lesson focus areas."""

suggest_lesson_focus(gaps: dict) -> list[str]
    """Suggest which standards to prioritize in upcoming lessons."""
```

---

## 7. Human-in-the-Loop Design

TeacherMind is designed with teacher oversight as a first principle:

- **No automatic sending** — all communications are drafts the teacher reviews
- **Confidence signals** — when the agent maps an assignment to a standard, it shows the mapping and confidence so the teacher can correct it
- **Explainable flags** — every at-risk flag includes the specific assignment(s) that triggered it
- **Editable outputs** — all drafted content is returned as editable text, not sent directly

---

## 8. Capstone Track Fit: Concierge Agents

TeacherMind fits the Concierge Agents track because it:

- Serves a specific individual user (the teacher) with personalized, context-aware assistance
- Proactively surfaces insights without the user having to query for them
- Operates across multiple connected tools (Canvas, Drive, standards data)
- Handles multi-step, multi-tool workflows (load grades → map standards → identify gaps → draft communication)
- Is built for ongoing, recurring use across a school year — not a one-off task

---

## 9. Evaluation Criteria

| Criterion | How TeacherMind addresses it |
|---|---|
| Agent demonstrates agentic behavior | Multi-tool coordination; proactive flagging; multi-step reasoning |
| Real-world utility | Direct reduction of teacher administrative burden |
| Responsible AI | Human-in-the-loop; no autonomous communication; explainable outputs |
| Technical implementation | ADK + Gemini + Cloud Run + Canvas API |
| Alignment with course concepts | Uses SDD specs, SKILL.md-style tool design, factory model for comms |

---

## 10. Stretch Goals (Post-Submission)

- Canvas OAuth flow (vs. manual token) for easier teacher onboarding
- Scheduled weekly digest: every Sunday, agent emails the teacher a class health summary
- Guided notes → standard tagging via document upload + LLM extraction
- Multi-class support (multiple periods, multiple grade levels)
- Arizona AIMS/AzMERIT assessment result integration for longitudinal tracking
