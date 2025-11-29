"""Prompt enhancement agent using the new flock blackboard architecture.

This agent consumes PromptEnhanceRequest artifacts and publishes
EnhancedPrompt artifacts to the blackboard.
"""

from flock import Flock

from pyros_cli.models.flock_artifacts import PromptEnhanceRequest, EnhancedPrompt


DESCRIPTION = """
An agent that enhances user prompts for image generation.

The agent takes a user prompt and optional instructions, then enhances it by:
- Adding rich visual details (lighting, composition, atmosphere)
- Incorporating artistic style descriptors
- Optimizing for image generation model comprehension
- Following best practices for prompt engineering

The resulting enhanced prompt will produce stunning, high-quality images
when used with ComfyUI or similar image generation systems.
"""


def register_enhance_agent(flock: Flock) -> None:
    """Register the enhance agent with the flock orchestrator.
    
    Args:
        flock: The Flock orchestrator instance to register with.
    """
    (
        flock.agent("enhance_agent")
        .description(DESCRIPTION)
        .consumes(PromptEnhanceRequest)
        .publishes(EnhancedPrompt)
    )
