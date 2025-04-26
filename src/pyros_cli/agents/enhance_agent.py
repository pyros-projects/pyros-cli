from flock.core import FlockFactory

DESCRIPTION = """
An agent that enhances user prompts.
The agent will take a user prompt and user instruction and enhance it by adding more details, context, and other information.
The resulting enhanced prompt when used with an image generation model will result in an absolutely stunning image.
The agent adheres to best practices for prompt engineering for image generation and generates perfect prompts.
"""

def create_enhance_agent():
    agent = FlockFactory.create_default_agent(
        name="enhance_agent",
        description=DESCRIPTION,
        input="user_prompt: str, user_instruction: str",
        output="enhanced_prompt: str",
    )

    return agent