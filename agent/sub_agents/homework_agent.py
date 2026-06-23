from google.adk import Agent
from agent.voice_tools import VOICE_TOOL_REGISTRY

homework_specialist = Agent(
    name="homework_specialist",
    model="gemini-2.5-flash",
    tools=[VOICE_TOOL_REGISTRY["generate_spiral_homework"]],
    instruction="You are the Spiral Homework Specialist. When asked to generate homework, use your tool and return the resulting Drive link.",
    description="Generates spiral homework for Karrie."
)
