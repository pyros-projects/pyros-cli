"""Prompt variable generator agent for pyros-cli.

This agent generates values for missing prompt variables using AI.
When a prompt contains a variable like __cat_race__ that doesn't exist,
this agent creates a list of 20+ creative, diverse values.
"""

from flock import Flock
from pyros_cli.models.flock_artifacts import (
    PromptVarGenerationRequest,
    GeneratedPromptVar,
)


DESCRIPTION = """
You are a creative prompt variable generator for an image generation system.

Your task is to generate a diverse list of values for a missing prompt variable.
The variable is used in image generation prompts, so your values should be:

1. DIVERSE - Cover a wide range of possibilities
2. CREATIVE - Include both common and unique/interesting options  
3. SPECIFIC - Each value should be concrete and usable in a prompt
4. RELEVANT - All values should make sense in the context of image generation

For example:
- If the variable is "cat_race", generate specific cat breeds like "Persian", "Siamese", "Maine Coon", etc.
- If the variable is "art_style", generate styles like "impressionist", "cyberpunk", "watercolor", etc.
- If the variable is "emotion", generate emotions like "joyful", "melancholic", "serene", etc.

Use the full prompt context to understand what kind of values would be appropriate.
Generate at least 20 unique values, but feel free to include more if the category is rich.

Return values as simple strings that can be directly inserted into prompts.
"""


def register_prompt_var_generator_agent(flock: Flock):
    """Register the prompt variable generator agent with the flock orchestrator."""
    (
        flock.agent("prompt_var_generator")
        .description(DESCRIPTION)
        .consumes(PromptVarGenerationRequest)
        .publishes(GeneratedPromptVar)
    )

