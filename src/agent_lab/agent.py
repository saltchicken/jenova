from google.adk import Workflow
from google.adk.events import RequestInput

def collect_info():
    yield RequestInput(
        message="Please provide your 6-digit account PIN:", 
        response_schema=int
    )

def process_account(node_input):
    return f"Processing account: {node_input}"

root_agent = Workflow(
    name="agent_lab",
    edges=[('START', collect_info, process_account)]
)
