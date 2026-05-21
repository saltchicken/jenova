from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.models.lite_llm import LiteLlm

# 1. Define the Code Writer
code_writer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_writer_agent",
    description="Writes the initial code based on the user request.",
    instruction="""
    You are an expert programmer. Write clean, functional code to solve the user's prompt. 
    Only output the code and necessary comments.
    """
)

# 2. Define the Code Reviewer
code_reviewer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_reviewer_agent",
    description="Reviews code for bugs and best practices.",
    instruction="""
    Review the code provided to you. Identify any bugs, security flaws, 
    or areas for optimization. List the required changes clearly.
    """
)

# 3. Define the Code Refactorer
code_refactorer = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_refactorer_agent",
    description="Applies feedback and outputs the final refactored code.",
    instruction="""
    You are a code refactorer. Take the original code and the reviewer's feedback, 
    and output the final, optimized version of the code.
    """
)

code_output_formatter = Agent(
    model=LiteLlm(model="ollama_chat/devstral-small-2"),
    name="code_output_formatter_agent",
    description="Takes the final refactored code and outputs it in the proper format",
    instruction="""
    You are a code output formatter. Take the final refactored code and output only the code.
    Do not include any explanation or anything else.
    """
)


# 4. Define the Sequential Pipeline
agent = SequentialAgent(
    name="coder_agent",
    description="Executes a sequence of code writing, reviewing, and refactoring.",
    sub_agents=[code_writer, code_reviewer, code_refactorer, code_output_formatter]
)
