# Migration to Google Agent Development Kit (ADK)

## 1. Overview
This document outlines the shift from a manual Gemini SDK implementation to a formal Agent Development Kit (ADK) architecture for TeacherMind. 

The original implementation (`agent/agent.py`) manually managed the agent lifecycle, including building `FunctionDeclaration` objects by hand, managing conversational history arrays, and running a `while` loop to manually extract and dispatch function calls to a `TOOL_REGISTRY`. 

By migrating to ADK, we adopt a higher-level abstraction that natively handles state management, tool dispatching, and schema generation, resulting in cleaner, more maintainable code.

## 2. Comparison: Current Workflow vs. ADK Workflow

### 2.1. Tool Definitions
**Current Workflow (Manual):**
Tools are currently defined as large dictionaries conforming to the Gemini API's JSON schema format (`genai_types.FunctionDeclaration`). Every time a tool's arguments change, both the python function and the JSON schema must be manually synced.
```python
# Old way
TOOLS = [{
    "function_declarations": [{
        "name": "load_grade_export",
        "description": "Load and normalize a Synergy CSV...",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string"}
            },
            "required": ["filepath"]
        }
    }]
}]

def load_grade_export(filepath: str) -> dict:
    ...
```

**ADK Workflow:**
Using ADK, tools are defined directly from Python functions via a decorator (`@agent_tool` or similar). ADK uses the function's type hints and docstrings to automatically generate the required JSON schema, completely eliminating the duplicate boilerplate.
```python
# New ADK way
@agent_tool
def load_grade_export(filepath: str) -> dict:
    """Load and normalize a Synergy CSV grade export.
    Args:
        filepath: Path to the Synergy CSV file.
    """
    ...
```

### 2.2. The Agent Execution Loop
**Current Workflow (Manual):**
The conversation loop manually handles API responses, tracks `history` using `genai_types.Content`, and iterates over parts to find `function_call` fields. It then manually looks up the function in a `TOOL_REGISTRY`, executes it, and sends the `function_response` back to the model in another API call.

**ADK Workflow:**
ADK abstracts the loop away into an `Agent` class. You instantiate the Agent with your configured tools and system prompt. When you pass a user message to the agent, it handles the function calling loop automatically internally.
```python
# New ADK way
agent = Agent(
    model="gemini-2.0-flash",
    system_instruction=SYSTEM_PROMPT,
    tools=[load_grade_export, analyze_grade_trends, ...],
)

response = agent.run("Who is struggling in Period 2?")
print(response.text)
```

## 3. Benefits of the Shift
1. **Less Boilerplate**: ~150 lines of JSON tool definitions in `agent.py` will be removed.
2. **Schema Safety**: Function arguments and their schemas are guaranteed to stay in sync because ADK derives the schema directly from the Python function signature.
3. **Easier Integration**: The Voice Console (`web/server.py`) can interact directly with the ADK `Agent` instance, allowing Nova to natively use tools over the live voice websocket without reinventing the tool loop.
4. **Readability**: `agent/agent.py` will be reduced to just the system prompt and configuration, rather than acting as a custom execution engine.
