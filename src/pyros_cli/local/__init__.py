"""Local standalone mode for pyros-cli.

This module provides offline image generation using:
- Z-Image-Turbo for image generation (via diffusers)
- Qwen3-4B for LLM tasks (via transformers)

No internet connection or ComfyUI required!
"""

from pyros_cli.local.cli import main

__all__ = ["main"]

