# Multi-Agent Orchestration Architecture

This document outlines the architectural tactic used to manage complex tasks (like building Homework, Group Activities, and Quizzes) in TeacherMind without overwhelming the conversational agent's memory window or processing power.

## The Problem
If the primary conversational agent (Nova) was forced to read the full 6th Grade AZ Math Standards, write a 10-page Word document, perform an LLM self-review on its own work, and interface with Google Drive, its context window would instantly bloat. This would cause Nova to become slow, lose track of the conversational thread with Karrie, and quickly exceed token limits.

## The Solution: Delegated Pipeline & Reflection Loop
To solve this, TeacherMind employs a **Delegated Pipeline Architecture** paired with a true **Multi-Agent Reflection Loop**. Nova acts purely as the **Conversational Orchestrator**, while entirely separate execution paths and specialized worker tools handle the heavy lifting.

### 1. The Orchestrator (Nova)
Nova operates via the Gemini Live API. Her sole responsibility is to maintain a fast, human-like voice conversation with Karrie. 
- She has access to a registry of tools (`agent/voice_tools.py`).
- When Karrie makes a complex request (e.g., *"Nova, build a weekly quiz and a DOK group activity for Expressions and Equations"*), Nova does **not** generate the content in her chat memory.
- Instead, she recognizes the intent and triggers specialized worker tools (`generate_weekly_quiz` and `generate_dok_activity`).

### 2. Specialized Worker Tools (The Pipeline)
Each content generator tool is an independent Python script.
- **Total Independence:** When triggered, a tool like `weekly_quiz.py` spins up its *own* fresh instance of the Gemini API (`gemini-2.5-flash`).
- **Deep Context:** It fetches the dense AZ Math standards securely via the local **Curriculum MCP Server**.
- **Side Effects:** The worker tool handles all side effects autonomously: rendering the `.docx` file, authenticating with Google Drive, uploading the document into the `01_Drafts` folder (waiting for Karrie to move it to `02_Approved`), and triggering the **Comms MCP Server** to email Karrie.

### 3. The True Multi-Agent Collaboration: The Pedagogy Reflection Loop
The marquee multi-agent interaction in TeacherMind occurs *inside* the worker pipeline.
Before any draft is saved to Drive, the generator model hands its output to the **Pedagogy Critic** (`pedagogy_critic.py`)—a completely distinct agent prompt and LLM call. 
- **Agent 1 (Generator):** Drafts the curriculum based on MCP standards.
- **Agent 2 (Critic):** Performs an LLM self-review/critique against DOK levels and alignment, returning a structured verdict.
- **Agent 1 (Generator):** Revises its draft based on the Critic's feedback.
This generator → critic reflection loop is the core multi-agent pattern that guarantees high-quality, aligned output without needing the Orchestrator to oversee the revision process.

### 4. The Return Handoff
Once the pipeline finishes its massive, multi-step execution (including MCP consumption and the multi-agent reflection loop), it returns a simple, tiny success string back to the Orchestrator (e.g., *"Success, quiz generated and uploaded to this Drive Link"*). 

## Why This Tactic is Perfect
By explicitly walling off the heavy generation tasks into separate execution pipelines:
1. **Performance:** Nova remains incredibly fast and responsive for real-time voice interactions.
2. **Context Purity:** Nova doesn't clutter her short-term memory with thousands of tokens of AZ math standards or Word Document markdown formatting.
3. **Scalability:** We can infinitely expand TeacherMind's capabilities (e.g., adding an IEP generator, a parent email drafter, or a data analytics dashboard) without ever making Nova "heavier." She just gets a new tool added to her belt. 
4. **Security:** Worker tools can be given scoped, least-privilege credentials (like the Gmail API token) that the conversational UI never needs to see or manage directly.
