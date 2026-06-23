from google.adk import Agent
from agent.voice_tools import VOICE_TOOL_REGISTRY

quiz_specialist = Agent(
    name="quiz_specialist",
    model="gemini-2.5-flash",
    tools=[VOICE_TOOL_REGISTRY["generate_weekly_quiz"]],
    instruction="You are the Weekly Quiz Specialist. When asked to build a quiz, use your tool and return the resulting Drive link.",
    description="Generates weekly quizzes for Karrie."
)
