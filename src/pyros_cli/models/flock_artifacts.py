"""Flock artifact type definitions for pyros-cli.

These Pydantic models define the typed artifacts that flow through the
blackboard architecture. Each model decorated with @flock_type becomes
a registered artifact type that agents can consume and publish.
"""

from pydantic import BaseModel, Field
from flock.registry import flock_type


@flock_type
class PromptEnhanceRequest(BaseModel):
    """Input artifact requesting prompt enhancement.
    
    This is published to the blackboard to trigger the enhance_agent.
    """
    user_prompt: str = Field(
        description="The original prompt from the user to be enhanced"
    )
    user_instruction: str = Field(
        default="",
        description="Additional instructions for how to enhance the prompt"
    )


@flock_type
class EnhancedPrompt(BaseModel):
    """Output artifact containing the enhanced prompt.
    
    Published by the enhance_agent after processing a PromptEnhanceRequest.
    """
    enhanced_prompt: str = Field(
        description="The enhanced, detailed prompt optimized for image generation"
    )
    original_prompt: str = Field(
        default="",
        description="The original prompt that was enhanced (for reference)"
    )

