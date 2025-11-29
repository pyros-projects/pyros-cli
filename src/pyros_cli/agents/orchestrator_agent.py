"""Orchestrator agent using the new flock blackboard architecture.

This agent can use tools to process requests and coordinate
prompt enhancement workflows.
"""

from typing import Callable

from flock import Flock

from pyros_cli.models.flock_artifacts import PromptEnhanceRequest, EnhancedPrompt


DESCRIPTION = """
An orchestrator agent that coordinates prompt enhancement workflows.

This agent:
- Receives prompt enhancement requests
- Can utilize tools for additional processing
- Produces enhanced prompts optimized for image generation
"""


def register_orchestrator_agent(
    flock: Flock, 
    tools: list[Callable] | None = None
) -> None:
    """Register the orchestrator agent with the flock orchestrator.
    
    Args:
        flock: The Flock orchestrator instance to register with.
        tools: Optional list of tool functions the agent can use.
    """
    builder = (
        flock.agent("orchestrator_agent")
        .description(DESCRIPTION)
        .consumes(PromptEnhanceRequest)
        .publishes(EnhancedPrompt)
    )
    
    if tools:
        builder.with_tools(tools)
