from flock.core import Flock, flock_tool
from pyros_cli.agents.enhance_agent import create_enhance_agent
from pyros_cli.services.config import load_config

config = load_config()

@flock_tool
def enhance_prompt(prompt: str, user_instruction: str):
    """Enhance a prompt using an AI agent"""
    flock = Flock(show_flock_banner=False, model=config.model_name)
    flock.add_agent(create_enhance_agent())
    result = flock.run("enhance_agent", input={"user_prompt": prompt, "user_instruction": user_instruction})
    return result
