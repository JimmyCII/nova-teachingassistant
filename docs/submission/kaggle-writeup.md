# Kaggle Submission Writeup: TeacherMind (Nova)

**Track:** Concierge Agents · **Author:** Jim Cockerham
**Course:** 5-Day AI Agents: Intensive Vibe Coding Course with Google

### Links & Demo
- 🎥 **Meet Nova (persona interview):** https://youtu.be/oTBeDFI9uh0
- 🛠️ **Technical demo — Nova does the work:** https://youtu.be/ahygLV0LRl4 *(voice/UI request → live agent tool calls → Drive artifact + approval email)*
- 🌐 **Live voice console (Cloud Run):** `nova-voice-console` (`us-central1`) — *[paste public URL]*
- 💻 **Source:** *[paste GitHub repo URL]*

---

## 1. Problem Definition
Middle school educators face an overwhelming administrative burden, often juggling siloed systems for grading, curriculum planning, and parent communication. For Karrie, a veteran 6th-grade math teacher in Arizona, this fragmentation consumes hours of her week—time that could be spent directly impacting students. Current AI tools are too generic; they make a veteran teacher bend to the tool. They lack any understanding of her specific state standards (AZ Math Standards), her pedagogical style (Webb's Depth of Knowledge), and her established classroom voice.

TeacherMind (featuring the voice agent **Nova**) was built to solve this. Nova acts not as a replacement, but as an apprentice—a concierge agent that understands Karrie's specific context, generates standards-aligned content (homework, quizzes, and DOK small-group activities), and formats it directly into her native workflow (Google Drive) for review. Nova learned Karrie's *craft*, never her students' data.

## 2. Solution Design
TeacherMind is built on a **Dual-MCP Architecture** and a **Voice-First Multi-Agent Content Pipeline**:
- **Voice Orchestration:** The frontend is a FastAPI + Gemini Live API WebSocket bridge that allows Karrie to talk to Nova hands-free from her phone or laptop, with an audio-reactive arc-reactor "core" in her colors. The live console is wired to **18 tools** (grades, standards, Canvas, parent comms, spiral homework, DOK activities, weekly quiz, request log).
- **Multi-Agent Pipeline:** Instead of relying on a single prompt to generate complex artifacts like a math quiz, TeacherMind uses a collaborative pipeline. A specialist agent generates the draft, and a **Pedagogy Critic** agent subsequently reviews the draft against AZ Math Standards and DOK rigor before it is finalized.
- **Content generators (live-verified):** a spiral homework generator (Gemini spiral mix → editable `.xlsx` in Karrie's 4-column format → Drive `Drafts`), a DOK group-activity generator (DOK 1–3 leveled, with group roles), and a 10-question weekly quiz generator with answer key—each uploaded to Drive for review.
- **Model Context Protocol (MCP):**
  - `Curriculum MCP`: Exposes state standards (`standards://az-math-6`) and the Webb DOK model (`dok://webb-model`) as native resources for the agents to pull from.
  - `Comms MCP`: Senses changes in Google Drive and triggers approval emails.
- **Human-in-the-Loop:** When Nova generates a quiz or homework assignment, she doesn't publish it directly. Instead, she uploads the draft to Google Drive and emails Karrie a link. Karrie reviews the document and simply drags it into an approved folder, which the system senses and marks as approved—no new dashboard to learn.

## 3. Effective Use of Agent Technologies
This project applies four core agentic concepts demonstrated in the course:
1. **Model Context Protocol (MCP) Integration:** We built and actively consume two distinct FastMCP servers. The Pedagogy Critic dynamically reads the `standards://az-math-6` resource from the Curriculum MCP to grade generated content, and the Comms MCP drives the Drive-watch approval loop—proving real interoperability, not a stub.
2. **Multi-Agent Collaboration (Dual-Path Orchestration):** We avoided monolithic prompts by splitting generation and grading into separate specialist agents (`generator` → `pedagogy_critic`). To maximize both structure and speed, we implemented a **dual-path orchestrator**:
   - *Formal ADK Path:* For deep, asynchronous planning tasks, the repository features a fully functional Google ADK Orchestrator (`agent/adk_orchestrator.py`)—a root *Nova* agent that strictly manages state and routes via `transfer_to_agent` to Homework, Quiz, and DOK sub-agents. A live smoke test (`tests/test_adk_routing.py`) confirms the full loop: Nova routes to the DOK specialist for `6.NS.A.1`, builds the activity, uploads it to Drive, and fires the HITL approval email. The latency analysis is documented in `docs/architecture/ADK_LATENCY_TEST_AND_JUSTIFICATION.md`.
   - *Low-Latency Voice Path:* To keep Nova a highly responsive, voice-first companion Karrie can use on the go, we exposed these same agentic capabilities as direct function-calling tools injected into the Gemini Live API WebSocket—one network hop instead of the ADK event loop's 3–5s handoff silence. This proves we can leverage the formal ADK's structure for heavy lifting while adapting multi-agent concepts to strict real-time mobile constraints.
3. **Agentic Approval Loop:** By wiring the `Comms MCP` to watch Google Drive folder state, we created a seamless Human-in-the-Loop (HITL) system that respects the teacher's final authority without requiring her to log into a new dashboard.
4. **Spec-Driven Development:** A strong, well-documented spec trail (`CAPSTONE_SPEC.md`, `docs/specs/`, `docs/architecture/`, and the decision/routing-audit logs) traces every major component from spec to implementation.

## 4. Implementation Quality
- **Security First & Judging Safety Gates:** The voice WebSocket spends the API key, so it enforces a same-origin **Origin check** (anti-CSWSH) and a constant-time **HMAC `CONSOLE_TOKEN`** check when exposed beyond localhost. To prevent token-exhaustion attacks, a strict 15-turn-per-session cap forcefully drops abusive sessions and emails the system administrator. To safely share the live demo with the judging panel without exposing an unbounded attack surface, we deployed a "Blast Radius" containment strategy: the URL is token-gated, it runs on an isolated disposable API key, the Cloud Run container is capped at `--max-instances=2` to physically prevent scale-out billing spikes, and a $5.00 GCP billing alert ensures strict budget control.
- **Test-Driven:** The core logic is backed by **22 passing tests** (`pytest`) spanning grade tools, the Comms server, the Pedagogy Critic, and the spiral-homework pipeline (models, generator, renderer, Drive store, orchestrator), plus live ADK-routing and approval-loop smoke tests.
- **Cloud Run Deployment:** The system is containerized via Docker and **deployed to Google Cloud Run** (`nova-voice-console`, `us-central1`), with the Gemini key held in Secret Manager—so the teacher can reach the voice assistant securely from her mobile device in the classroom.
- **Data Privacy / FERPA:** Hardcoded guardrails prevent the agent from ever requesting or hallucinating student Personally Identifiable Information (PII). All committed sample/test data is synthetic; no real student data passes through the console. Nova was built from a teacher's *craft*, never her students' records.

## 5. Overall User Value
TeacherMind respects the "North Star" of education: the teacher stays in control. Nova doesn't try to teach the kids; she hands Karrie the tools she needs to shine. By generating DOK-leveled questions and standards-aligned homework natively as `.xlsx` / Markdown saved directly to her Drive, TeacherMind eliminates the friction of copying and pasting from a standard chatbot. It meets the teacher exactly where she already works, significantly reducing her administrative load so she can focus on what matters most—her students. As Nova puts it: *she shines the kids; I just hand her the cloth.*

*Nova is an AI persona built from Karrie's work—not Karrie herself.*
