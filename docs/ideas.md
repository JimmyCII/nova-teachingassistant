# Ideas Backlog — TeacherMind / Nova

Running capture of ideas. Not commitments — raw material for future brainstorming. Each idea notes
which build block it touches (1 Knowledge base · 2 Homework gen · 3 DOK builder · 4 Proficiency ·
5 Deployment/UX) and open questions. Add freely; we'll triage in a brainstorming session.

---

## ⭐ North Star (the product principle that filters every idea)
**An easy application Karrie can actually implement — with Nova as her assistant.**
- **Zero learning curve.** Karrie has no time to learn a new tool. Nova must **meet her in the tools
  and habits she already has**, not ask her to adopt a new app/dashboard.
- **Save time + increase impact.** Every feature must give her back time *and/or* deepen her impact
  with students. If it does neither, cut it.
- **Human-in-the-loop.** Nova drafts/prepares/notifies; Karrie decides and acts. Never autonomous on
  anything outward-facing (parent comms, grades).
- **Litmus test for any idea:** "Could Karrie use this on a Tuesday with zero training, and would it
  save her real time?" If no → redesign or drop.

---

## Ideas

### 1. Give Nova its own Google account / identity  · Blocks 1, 5
Provision Nova a dedicated **Google (Workspace) account** so it can act with its own identity:
- **Create & save Google Docs** (lesson notes, parent letters, the weekly digest) into a shared Drive
  folder Karrie already opens.
- **Send email / notify Karrie** (e.g., "Here's your Sunday class-health digest," "3 retakes are
  overdue").
- Possibly **Calendar** (block planning time, remind of retake windows).
- *Considerations:* a Nova service/Workspace account + OAuth scopes (Drive, Gmail, Calendar);
  security (least-privilege, no student PII in Docs/email); cost (Workspace seat); clear "from Nova"
  identity so Karrie always knows it's the assistant. Drive/Docs is a strong fit for the **zero-
  learning-curve** rule — Karrie already lives in Google Docs.

### 2. Notify / communicate with Karrie where she already is  · Block 5
Karrie needs Nova to reach her without a new app.
- **Email** (via idea #1) — universal, zero learning curve. Strong default.
- **Text / SMS** — even lower friction for quick nudges (retake reminders, "Period 2 needs a re-teach
  on 6.NS.B.3"). Twilio or Google options.
- **Read-aloud / voice** — see `docs/research-voice-options.md` (Gemini Live API / Chirp 3).
- *Principle check:* prefer channels Karrie already checks daily.

### 3. Slack as a Nova ↔ Karrie (↔ Jim) channel  · Block 5  · ⚠ tension with North Star
Explore Slack as a lightweight chat surface to "talk to Nova."
- *Pro:* Slack is a clean, well-supported bot surface; great threaded history; Jim may already use it;
  good for *Jim* monitoring/QA of Nova during the build.
- *Con / open question:* **Karrie is NOT a Slack user** — adding Slack risks violating the
  zero-learning-curve rule for *her*. Options to resolve: (a) Slack for Jim/admin + email/SMS/voice
  for Karrie; (b) only adopt Slack if it truly replaces something, not adds; (c) skip Slack for
  Karrie entirely and use Google/SMS/voice. **Decide who the Slack user actually is before building.**

### 4. Nova lives inside Karrie's existing workflow (umbrella idea)  · All blocks
Rather than a destination app, Nova shows up as: a Doc that appears in her Drive, an email digest, a
text reminder, or a voice you can talk to — all from one agent. The "application" Karrie implements is
really *"check your email / open the Doc / say hey Nova,"* nothing new to learn.

### 5. Weekly proactive digest  · Blocks 1, 5  (already stubbed: `draft_class_digest`)
Every Sunday, Nova emails Karrie a summary of the upcoming plan and targeted level of student progress: who's at-risk by standard, what to re-teach,
upcoming Canvas assignments, overdue retakes. Concierge-style proactivity (matches CAPSTONE_SPEC
stretch goal). Tool already exists — needs a channel (email) + a schedule.

---

### 6. [COMPLETED] Nova's visual layer — a "Jarvis-style" voice console in Karrie's colors  · Block 5
A web-based console Karrie can **talk to**, built to introduce Nova to her. Elements:
- A **central animated voice orb / visualizer** that reacts as Nova listens and speaks.
- A **live transcript** of the conversation, and a few quick actions.
- **Voice** via Gemini Live API (see `docs/research-voice-options.md`).
- Deploy the agent in **ADK** (Jim's stated primary goal).

Branded in **Karrie's real palette** (validated from her persona/wardrobe — purple/violet is genuinely
her color):
| Role | Hex |
|------|-----|
| Deep Plum | `#3A1F4B` |
| Eggplant | `#522D69` |
| Amethyst | `#8750A6` |
| Lavender | `#DECCEA` |
| Warm Cream | `#FFF6E5` |
| Soft Peach | `#F7D4B0` |
| Milestone Gold | `#DDA440` |
| Soft Rose | `#AE4E6C` |

*Goal:* a delightful, zero-learning-curve first experience to **introduce Nova to Karrie**. Capabilities
(homework/DOK) get finalized **with her** afterward (samples + Drive organization). Build with the
`frontend-design` skill; responsive so it works on phone + computer.

### 7. Speaker awareness — know who's talking; meet & remember people  · Blocks 1, 2, 5
Nova should tell whether it's **Karrie or someone else**, let Karrie **introduce Nova to others**,
**record their names**, and address each person correctly (don't call everyone "Karrie"). Two layers:
- **Now — conversational (no biometrics, easy):** stop assuming the speaker is Karrie. Greet
  neutrally / ask who it's talking with; when someone is introduced ("Nova, this is my husband Jim"),
  remember and use that name for the rest of the session (the Live session already retains context).
  Cross-session memory of people needs a small store (tie to Nova's Google account / Drive, idea #1).
- **Later — voice biometrics (harder):** truly auto-detecting "this is Karrie's voice vs. a new
  voice" needs a **speaker-recognition/verification** model (voice embeddings + a short enrollment of
  Karrie's voice). This is **NOT native to the Gemini Live API** — it would require a parallel
  speaker-ID pipeline. (Cloud Speech-to-Text *diarization* labels "speaker 1 / speaker 2" but not who
  they are; identity needs enrollment.) Revisit after the core assistant works.
- **Quick win available now:** adjust Nova's system prompt so it no longer hard-codes the user as
  Karrie — greet warmly, and use a person's name only once it's known/introduced.

### 8. May-the-4th easter egg — Nova goes full Vader on May 4th  · flourish, low priority
On May 4th (Star Wars Day), Nova greets in playful **Darth Vader** mode and the orb briefly glows
lightsaber-red — a nod to Karrie dressing as Vader that day ("more Vader than Jedi"). Pure delight;
keep Nova warm underneath.

---

## Current direction (Jim, 2026-06-21)
**Near-term primary achieved:** Deployed the agent to Cloud Run + built a Jarvis-style visual layer (idea #6) + voice. We also completed the initial capabilities for Spiral Homework, DOK Group Activities, and Weekly Quizzes. 
**Next Up:** True zero-friction integration (Canvas LMS + Proactive Sunday Email Digests).

## Triage notes
- Idea #6 (Voice Console) and core Homework/DOK/Quiz features are **[COMPLETED]**.
- Ideas #1 (Google Account), #2 (Notifications), #4 (Workflow integration), and #5 (Weekly Digest) align tightly with the North Star (meet her where she is) and **[NEED SPEC]**.
- Idea #3 (Slack) needs a "who is the user" decision first — likely drop for Karrie per zero-learning-curve rule.
- Idea #7 (Speaker Awareness) **[NEEDS SPEC]**.
- All outward comms stay human-in-the-loop and PII-safe (no student data in Docs/email/Slack/SMS).
