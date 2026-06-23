# Capstone Push: Multi-Agent Pipeline & MCP Server

This plan addresses the two major architectural gaps required for a successful Kaggle Capstone submission (due July 6th): the **Multi-Agent Orchestration** and the **Model Context Protocol (MCP) Server**, while also updating the quiz format to Karrie's preferences.

## 1. Quiz Generator Updates (DOK 2 + Word Document)
- **Content:** Update the `generate_weekly_quiz` prompt to strictly request **4-5 questions** targeting the **DOK 2 level**.
- **Format:** We will use the `python-docx` library (which is already installed in your environment) to programmatically convert the LLM's Markdown output into a beautifully formatted Microsoft Word (`.docx`) file.
- **Drive Upload:** The Google Drive uploader will be updated to handle the `application/vnd.openxmlformats-officedocument.wordprocessingml.document` mime type so it uploads natively as a Word doc.

## 2. Multi-Agent Orchestration: The Pedagogy Critic
To demonstrate true multi-agent collaboration (not just routing), we will build the **Pedagogy Critic** agent defined in the spec:
- Create `agent/tools/pedagogy_critic.py`.
- **The Pipeline:** Instead of the Quiz tool immediately saving its draft, it will pass its generated text to the Pedagogy Critic.
- **The Critic's Job:** The Critic will use a separate Gemini call (acting as a strict peer reviewer) to verify that the questions are actually DOK 2, aligned to 6th-grade math, and free of PII. 
- **The Loop:** If the Critic finds flaws, it will return feedback to the Generator to revise. If it passes, it moves to the `.docx` renderer.

## 3. The Curriculum MCP Server
To demonstrate the MCP course concept, we will stand up the **Curriculum/Drive MCP Server**:
- Scaffold a FastMCP server in a new folder: `mcp/curriculum_server/server.py`.
- **Resources:** Expose the AZ Math 6 standards and DOK Webb Model as MCP Resources (`standards://az-math-6` and `dok://webb-model`).
- **Tools:** Expose the `save_draft` tool via MCP, wrapping our existing `GoogleDriveClient`. 
- **Wiring:** We will wire the Pedagogy Critic to read from this MCP server, proving that your multi-agent pipeline is consuming standardized MCP data.

## Verification Plan
1. **Quiz Test:** Run "Hey Nova, create a weekly quiz". Verify the console shows the Pedagogy Critic reviewing the draft, and verify a `.docx` file appears in Google Drive.
2. **MCP Test:** Start the MCP server over stdio and use an MCP Inspector/Client to list the tools and resources to prove the architecture works.

## User Review Required
> [!IMPORTANT]
> This is a heavy architectural lift but it perfectly aligns with the Capstone requirements. Are you comfortable with me building out the Pedagogy Critic and the MCP Server exactly as outlined above?
