from google.adk import Workflow
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import uvicorn

from jenova.graph import root_agent
from jenova.nodes import answer_question
from jenova.nodes import classify_intent
from jenova.nodes import handle_other
from jenova.nodes import take_action

# --- QUICK FIX FOR ADK EXPERIMENTAL A2A BUG ---
# Pydantic prevents adding fields to 'Workflow' dynamically.
# We bypass this by creating a quick subclass that explicitly expects them.


class PatchedWorkflow(Workflow):
    sub_agents: list = []
    instruction: str = ""


# Clone your existing graph into the patched workflow
a2a_root = PatchedWorkflow(
    name=root_agent.name,
    edges=root_agent.edges,
    sub_agents=[classify_intent, take_action, answer_question, handle_other],
    instruction=(
        "Jenova is a helpful AI assistant. She can answer general questions "
        "and has access to tools to control smart home room lights."))
# ----------------------------------------------

# Pass the patched workflow to the A2A builder
app = to_a2a(a2a_root, port=8000)

if __name__ == "__main__":
    # Run the A2A compliant server
    uvicorn.run(app, host="0.0.0.0", port=8000)
