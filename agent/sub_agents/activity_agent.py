from google.adk import Agent
from agent.voice_tools import VOICE_TOOL_REGISTRY

dok_specialist = Agent(
    name="dok_specialist",
    model="gemini-2.5-flash",
    tools=[VOICE_TOOL_REGISTRY["generate_dok_activity"]],
    instruction="You are the DOK Group Activities Specialist. When asked to build an activity, use your tool and return the resulting Drive link.",
    description="Generates DOK group activities for Karrie."
)
