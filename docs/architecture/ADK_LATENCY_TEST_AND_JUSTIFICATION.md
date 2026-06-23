# ADK Routing Test & Latency Justification

**Date:** 2026-06-22
**Component:** `adk_orchestrator.py` vs. `web/server.py`

## 1. Overview
TeacherMind relies on a complex multi-agent pipeline to generate standards-aligned curriculum (drafting, pedagogy review, and DOK alignment). We initially built this pipeline using the formal **Google Agent Development Kit (ADK) Orchestrator**. 

However, because the primary user interface is a real-time **Voice Console** (accessed via mobile device by a teacher in the classroom), strict ultra-low latency requirements forced a divergence in the architecture. This document captures the successful test of the formal ADK Orchestrator, the observed latency bottlenecks, and the justification for the final "Dual-Path" architecture.

---

## 2. ADK Orchestrator Smoke Test Outcome

To verify that our formal ADK logic (`adk_orchestrator.py`) functioned correctly, we ran a live smoke test against the Gemini API (`test_adk_routing.py`).

**Command Executed:**
```bash
python tests/test_adk_routing.py
```

**Test Output:**
```text
=========================================
 ADK ORCHESTRATOR LIVE SMOKE TEST
=========================================

[1/2] Testing Basic Persona & Initialization...
Sending message...
Nova's Response:
Hello! I'm TeacherMind, your AI concierge. I'm here to help you...
[SUCCESS] Basic Initialization Passed!

[2/2] Testing Multi-Agent Routing (Sub-Agent Handoff)...
Asking Nova to build a DOK Activity for 6.NS.A.1...
[Orchestrator Activity] Routing to tool: transfer_to_agent
[Orchestrator Activity] Routing to tool: generate_dok_activity
REAL EMAIL: Sending approval request to redacted@example.com for Fractions_DOK_Activity.md
Comms Loop executed: Email sent successfully to redacted@example.com (Message ID: 19ef1b9bc5d73b4b)
Nova's Final Response:
I've created a DOK group activity for Fractions targeting standard 6.NS.A.1. You can access it here: https://drive.google.com/file/d/...
[SUCCESS] Multi-Agent Routing Passed!
```

**Conclusion:** The formal ADK Orchestrator is fully functional. It successfully managed state, routed to the correct specialist sub-agent via `transfer_to_agent`, executed the tool to build the DOK activity, uploaded it to Drive, and utilized the Comms MCP to send an email for Human-in-the-Loop approval.

---

## 3. The UX Bottleneck: Latency in Voice Interactions

While the ADK Orchestrator proved extremely capable for deep, asynchronous planning tasks, we discovered a critical UX bottleneck when integrating it with the **Gemini Live API** (the WebSocket driving our voice console).

**The Latency Problem:**
The formal ADK Orchestrator relies on an internal event loop to process state handoffs (e.g., `Orchestrator -> transfer_to_agent -> Sub-Agent -> Orchestrator`). While this takes only a few seconds, a 3-to-5 second silence during a real-time voice conversation completely breaks the illusion of a highly responsive, conversational co-teacher. If Karrie asks Nova a question on her phone, Nova must respond almost instantly.

---

## 4. Architectural Justification: The Dual-Path Model

To solve the latency issue without sacrificing the agentic capabilities we built, we finalized a **Dual-Path Orchestration** architecture:

1. **Formal ADK Path (`agent/adk_orchestrator.py`)**: Maintained in the repository as the structural backbone for deep, asynchronous curriculum generation where response time is not critical.
2. **Low-Latency Voice Path (`web/server.py`)**: For the live deployed application, we bypassed the heavy ADK router. Instead, we exposed the exact same backend agents as direct **function-calling tools** injected into the Gemini Live API's schema. 

**Why this is effective:**
By using a function-orchestrated approach in the frontend, Nova can handle the user's voice input, determine the intent, and trigger the specialist agent in a single network hop. This keeps the voice latency ultra-low, ensuring the app remains a frictionless, "on-the-go" tool for a busy teacher, while still demonstrating mastery of complex multi-agent handoffs.
