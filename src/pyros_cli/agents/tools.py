"""Tool functions for flock agents.

These tools are decorated with @flock_tool and can be used by agents
to perform specific tasks during their execution.
"""

import asyncio

from flock import Flock
from flock.registry import flock_tool

from pyros_cli.agents.enhance_agent import register_enhance_agent
from pyros_cli.models.flock_artifacts import PromptEnhanceRequest, EnhancedPrompt
from pyros_cli.services.config import load_config


@flock_tool
def enhance_prompt(prompt: str, user_instruction: str = "") -> str:
    """Enhance a prompt using an AI agent.
    
    This tool creates a flock instance, publishes a prompt enhancement
    request to the blackboard, and returns the enhanced result.
    
    Args:
        prompt: The original prompt to enhance.
        user_instruction: Optional instructions for how to enhance.
        
    Returns:
        The enhanced prompt string.
    """
    config = load_config()
    
    async def _run() -> str:
        flock = Flock(model=config.model_name)
        register_enhance_agent(flock)
        
        # Publish input artifact to blackboard
        request = PromptEnhanceRequest(
            user_prompt=prompt,
            user_instruction=user_instruction
        )
        await flock.publish(request)
        await flock.run_until_idle()
        
        # Retrieve result from blackboard
        results = await flock.store.get_by_type(EnhancedPrompt)
        if results:
            return results[0].enhanced_prompt
        return prompt  # Fallback to original if no result
    
    return asyncio.run(_run())
