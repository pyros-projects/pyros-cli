from flock.core import Flock

from pyros_cli.agents.orchestrator_agent import create_orchestrator_agent


def create_flock(model:str, prompt: str, agent_instruction: str):
    """Create a flock"""
    print(prompt)
    print(agent_instruction)

    # Create a flock
    flock = Flock(show_flock_banner=False, model=model)


    flock.add_agent(create_orchestrator_agent())

    result = flock.run("orchestrator_agent", input={"user_prompt": prompt, "user_instruction": agent_instruction})
    
    return result


