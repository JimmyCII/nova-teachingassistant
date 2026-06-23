"""
Standards mapper for TeacherMind.

Maps assignment names/descriptions to AZ Math Standard codes using
keyword matching with LLM fallback via Gemini.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types as genai_types


# ── Load Standards Data ────────────────────────────────────────────────────────

def _load_standards() -> dict:
    data_path = Path(__file__).parent.parent / "data" / "az_math_6_standards.json"
    with open(data_path) as f:
        return json.load(f)


def _load_keyword_map() -> dict:
    data_path = Path(__file__).parent.parent / "data" / "standard_keywords.json"
    with open(data_path) as f:
        return json.load(f)["keyword_map"]


def _build_standards_list(standards_data: dict) -> list[dict]:
    """Flatten standards JSON into a list of {code, description, priority}."""
    result = []
    for domain in standards_data["domains"]:
        for cluster in domain["clusters"]:
            for std in cluster["standards"]:
                result.append({
                    "code": std["code"],
                    "description": std["description"],
                    "domain": domain["name"],
                    "priority": domain["priority"],
                })
                if "sub" in std:
                    for sub in std["sub"]:
                        result.append({
                            "code": sub["code"],
                            "description": sub["description"],
                            "domain": domain["name"],
                            "priority": domain["priority"],
                        })
    return result


# ── Tools ──────────────────────────────────────────────────────────────────────

def get_all_standards() -> dict:
    """
    Return all AZ Grade 6 Math Standards as a structured list.

    Returns:
        dict with domains list, each containing standards with code, description, priority.
    """
    data = _load_standards()
    standards = _build_standards_list(data)
    return {
        "grade": 6,
        "state": "Arizona",
        "total_standards": len(standards),
        "standards": standards,
        "priority_breakdown": {
            "major": [s["code"] for s in standards if s["priority"] == "major"],
            "supporting": [s["code"] for s in standards if s["priority"] == "supporting"],
            "additional": [s["code"] for s in standards if s["priority"] == "additional"],
        },
    }


def get_standard_info(standard_code: str) -> dict:
    """
    Return detailed info for a specific standard code.

    Args:
        standard_code: AZ Math standard code (e.g., "6.NS.A.1" or "6.NS").

    Returns:
        dict with code, description, domain, priority, and related standards.
    """
    standards_data = _load_standards()
    all_standards = _build_standards_list(standards_data)

    # Exact match first
    for std in all_standards:
        if std["code"] == standard_code:
            return std

    # Domain-level match (e.g., "6.NS" returns all NS standards)
    domain_match = [s for s in all_standards if s["code"].startswith(standard_code)]
    if domain_match:
        return {
            "query": standard_code,
            "matched_standards": domain_match,
            "count": len(domain_match),
        }

    return {"error": f"Standard code '{standard_code}' not found."}


def map_assignment_to_standard(
    assignment_name: str,
    description: Optional[str] = None,
    use_llm: bool = True,
) -> dict:
    """
    Map an assignment name/description to the best-matching AZ Math Standard.

    First tries keyword matching. Falls back to Gemini LLM if no keyword match
    and use_llm=True.

    Args:
        assignment_name: Name of the assignment (e.g., "Fraction Division Quiz").
        description: Optional longer description for better matching.
        use_llm: Whether to use Gemini as a fallback (requires GOOGLE_API_KEY).

    Returns:
        dict with standard_code, description, priority, confidence, method.
    """
    keyword_map = _load_keyword_map()
    standards_data = _load_standards()
    all_standards = _build_standards_list(standards_data)

    text = f"{assignment_name} {description or ''}".lower()

    # ── Keyword matching ──────────────────────────────────────────────────────
    scores: dict[str, int] = {}
    for std_code, keywords in keyword_map.items():
        hit_count = sum(1 for kw in keywords if kw.lower() in text)
        if hit_count > 0:
            scores[std_code] = hit_count

    if scores:
        best_code = max(scores, key=lambda k: scores[k])
        std_info = next((s for s in all_standards if s["code"] == best_code), {})
        return {
            "standard_code": best_code,
            "description": std_info.get("description", ""),
            "domain": std_info.get("domain", ""),
            "priority": std_info.get("priority", ""),
            "confidence": "high" if scores[best_code] >= 2 else "medium",
            "method": "keyword",
            "keyword_hits": scores[best_code],
        }

    # ── LLM fallback ─────────────────────────────────────────────────────────
    if not use_llm:
        return {
            "standard_code": "unknown",
            "confidence": "low",
            "method": "none",
            "note": "No keyword match found. Enable use_llm=True for LLM classification.",
        }

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {
            "standard_code": "unknown",
            "confidence": "low",
            "method": "none",
            "note": "Set GOOGLE_API_KEY to enable LLM fallback.",
        }

    client = genai.Client(api_key=api_key)
    model_name = os.getenv("AGENT_MODEL", "gemini-2.0-flash")

    standards_str = "\n".join(
        f"{s['code']}: {s['description']}" for s in all_standards
    )

    prompt = f"""You are a 6th-grade Arizona math teacher's assistant.

Map this assignment to the most appropriate Arizona Mathematics Standard:

Assignment Name: "{assignment_name}"
{f'Description: "{description}"' if description else ""}

Available standards:
{standards_str}

Respond with ONLY a JSON object in this format:
{{"standard_code": "6.XX.X.X", "confidence": "high|medium|low", "reasoning": "brief explanation"}}
"""

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        text_resp = response.text.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("```")[1].lstrip("json").strip()
        result = json.loads(text_resp)
        result["method"] = "llm"
        std_info = next((s for s in all_standards if s["code"] == result.get("standard_code")), {})
        result["description"] = std_info.get("description", "")
        result["priority"] = std_info.get("priority", "")
        return result
    except Exception as e:
        return {
            "standard_code": "unknown",
            "confidence": "low",
            "method": "llm_error",
            "error": str(e),
        }
