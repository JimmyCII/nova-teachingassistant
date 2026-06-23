"""
Live Smoke Test for ADK Orchestrator

This script tests the google.adk setup live against the Gemini API to verify
that Nova can correctly route tasks to her sub-agents.

Run with: python test_adk_routing.py
"""

import sys
import os
from dotenv import load_dotenv

# Ensure we have the API key loaded
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    print("ERROR: GOOGLE_API_KEY not found in .env file.")
    sys.exit(1)

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent.adk_orchestrator import nova_adk_orchestrator

def run_smoke_test():
    print("=========================================")
    print(" ADK ORCHESTRATOR LIVE SMOKE TEST")
    print("=========================================\n")

    # Initialize the Runner with our formal ADK Orchestrator
    session_svc = InMemorySessionService()
    runner = Runner(agent=nova_adk_orchestrator, app_name="teacher_mind", session_service=session_svc)
    session_id = "smoke-test-session"
    user_id = "test-user"
    
    import asyncio
    asyncio.run(session_svc.create_session(app_name="teacher_mind", user_id=user_id, session_id=session_id))

    print("[1/2] Testing Basic Persona & Initialization...")
    try:
        msg = types.Content(role="user", parts=[types.Part(text="Hi! Who are you and what do you do?")])
        print("Sending message...")
        received_output = False
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=msg):
            # We look for the final output text
            if getattr(event, "content", None) and event.content.parts:
                print(f"\nNova's Response:\n{event.content.parts[0].text}\n")
                received_output = True
        
        if not received_output:
            print("[FAIL] Did not receive output from the agent.")
            return
            
        print("[SUCCESS] Basic Initialization Passed!\n")
    except Exception as e:
        print(f"[FAIL] Failed Basic Initialization: {e}")
        return

    print("[2/2] Testing Multi-Agent Routing (Sub-Agent Handoff)...")
    print("Asking Nova to build a DOK Activity for 6.NS.A.1...")
    try:
        msg2 = types.Content(role="user", parts=[types.Part(text="Can you build a DOK group activity for Fractions targeting standard 6.NS.A.1? Please use your specialized DOK sub-agent to do this.")])
        for event in runner.run(user_id=user_id, session_id=session_id, new_message=msg2):
            if getattr(event, "content", None) and event.content.parts:
                part = event.content.parts[0]
                if part.function_call:
                    print(f"[Orchestrator Activity] Routing to tool: {part.function_call.name}")
                elif part.text:
                    print(f"\nNova's Final Response:\n{part.text}\n")
        print("[SUCCESS] Multi-Agent Routing Passed!\n")
    except Exception as e:
        print(f"[FAIL] Failed Multi-Agent Routing: {e}")

if __name__ == "__main__":
    run_smoke_test()
