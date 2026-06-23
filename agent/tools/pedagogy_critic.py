from google import genai
from google.genai import types
from pydantic import BaseModel
import os
import json
from pathlib import Path

_CRITIC_MODEL = os.getenv("CRITIC_MODEL", "gemini-2.5-flash")

class CriticVerdict(BaseModel):
    verdict: str
    issues: list[str]
    revised_text: str
    standards_source: str

def _standards_via_mcp() -> str:
    from agent.tools.mcp_client import read_resource
    return read_resource("standards://az-math-6")

def review_and_revise(draft_text: str, content_type: str = "quiz", target_dok: int = 2,
                      _standards_provider=_standards_via_mcp) -> dict:
    """
    Acts as the Pedagogy/Standards Critic in the multi-agent pipeline.
    It takes a draft, evaluates it against DOK rigor and 6th grade math standards,
    and returns a structured revised verdict.
    """
    client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
    
    try:
        print("  [Critic] Fetching standards from MCP...")
        standards = _standards_provider()
        source = "mcp"
        print("  [Critic] Fetched standards successfully from MCP.")
    except Exception as e:
        # resilient fallback so the product never breaks — but the DEMO path must hit MCP
        print(f"Warning: MCP Server connection failed: {e}. Falling back to disk.")
        p = Path(__file__).resolve().parents[2] / "agent/data/az_math_6_standards.json"
        standards = p.read_text(encoding="utf-8") if p.exists() else "{}"
        source = "disk-fallback"

    system_instruction = f"""You are the Pedagogy/Standards Critic for a 6th-grade math teacher.
Your job is to review a draft {content_type} and strictly ensure it meets these requirements:
1. **DOK Rigor**: Questions must target Depth of Knowledge Level {target_dok}.
2. **6th Grade AZ Standards**: Must align with the standards provided below.
3. **Correct Answer Key**: Ensure the math is correct and an answer key is provided.
4. **PII Safety**: No real student names. Use fictional names if needed.

If the draft is good, improve its formatting and clarity. If it misses the DOK {target_dok} mark, rewrite the questions to match the rigor.

You must return a structured JSON response matching the schema. Do not include markdown formatting like ```json in the output.

Standards Reference:
{standards[:2000]}... (truncated for context)
"""
    
    prompt = f"Review and revise the following draft {content_type}:\n\n{draft_text}"
    
    try:
        print("  [Critic] Calling Gemini API for review...")
        response = client.models.generate_content(
            model=_CRITIC_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
                response_mime_type="application/json",
                response_schema=CriticVerdict,
            )
        )
        print("  [Critic] Gemini API returned successfully.")
        
        # Parse the JSON response
        result = json.loads(response.text)
        result["standards_source"] = source
        return result
    except Exception as e:
        print(f"Critic review failed: {e}")
        return {
            "verdict": "failed",
            "issues": [f"Critic agent crashed: {e}"],
            "revised_text": draft_text,
            "standards_source": source
        }
