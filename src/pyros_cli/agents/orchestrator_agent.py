from flock.core import FlockFactory
from pyros_cli.agents.tools import enhance_prompt

DESCRIPTION = """
An agent that executes the correct tool based on the user's request.
"""

def create_orchestrator_agent():
    agent = FlockFactory.create_default_agent(
        name="orchestrator_agent",
        description=DESCRIPTION,
        input="user_prompt: str, user_instruction: str",
        output="enhanced_prompt: str",
        tools=[enhance_prompt]
    )

    return agent