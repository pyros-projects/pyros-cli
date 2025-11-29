"""Flock orchestrator handler for pyros-cli.

This module provides the main interface for running flock-based
prompt enhancement workflows using the blackboard architecture.
"""

import asyncio
from typing import Any

from flock import Flock

from pyros_cli.agents.orchestrator_agent import register_orchestrator_agent
from pyros_cli.agents.enhance_agent import register_enhance_agent
from pyros_cli.models.flock_artifacts import PromptEnhanceRequest, EnhancedPrompt


async def run_flock_async(
    model: str, 
    prompt: str, 
    agent_instruction: str = ""
) -> str | None:
    """Run the flock orchestrator with the given prompt asynchronously.
    
    This function:
    1. Creates a Flock instance with the specified model
    2. Registers the enhance agent
    3. Publishes a PromptEnhanceRequest to the blackboard
    4. Waits for all agents to complete processing
    5. Returns the enhanced prompt from the blackboard
    
    Args:
        model: The LLM model identifier (e.g., "openai/gpt-4o").
        prompt: The user's original prompt to enhance.
        agent_instruction: Optional instructions for enhancement.
        
    Returns:
        The enhanced prompt string, or None if no result was produced.
    """
    flock = Flock(model=model)
    
    # Register the enhance agent
    register_enhance_agent(flock)
    
    # Create and publish the input artifact
    request = PromptEnhanceRequest(
        user_prompt=prompt,
        user_instruction=agent_instruction
    )
    await flock.publish(request)
    
    # Run until all agents complete
    await flock.run_until_idle()
    
    # Retrieve results from the blackboard
    results = await flock.store.get_by_type(EnhancedPrompt)
    if results:
        return results[0].enhanced_prompt
    
    return None


def create_flock(model: str, prompt: str, agent_instruction: str = "") -> Any:
    """Create and run a flock - synchronous wrapper for backwards compatibility.
    
    This is a convenience function that wraps the async workflow
    for use in synchronous contexts.
    
    Args:
        model: The LLM model identifier (e.g., "openai/gpt-4o").
        prompt: The user's original prompt to enhance.
        agent_instruction: Optional instructions for enhancement.
        
    Returns:
        The enhanced prompt string, or None if no result was produced.
    """
    return asyncio.run(run_flock_async(model, prompt, agent_instruction))
