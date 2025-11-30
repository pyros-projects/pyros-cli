"""Local image generator using Z-Image-Turbo.

This module provides image generation using the Z-Image-Turbo model
via the diffusers library. No ComfyUI or external services required!
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from rich.console import Console
from PIL import Image

console = Console()

# Lazy load the pipeline
_pipeline = None


def _get_model_path() -> str:
    """Get the Z-Image model path from env or use HuggingFace default."""
    return os.getenv("Z_IMAGE_PATH", "Tongyi-MAI/Z-Image-Turbo")


def _get_output_dir() -> Path:
    """Get the output directory for generated images."""
    output_dir = Path(os.getenv("LOCAL_OUTPUT_DIR", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _load_pipeline():
    """Lazy load the Z-Image pipeline.
    
    Automatically unloads the LLM to free GPU memory,
    since both models cannot fit in VRAM simultaneously.
    """
    global _pipeline
    
    if _pipeline is not None:
        return _pipeline
    
    # Unload LLM first to free GPU memory
    try:
        from pyros_cli.local import llm_provider
        if llm_provider._model is not None:
            console.print("[dim]Unloading LLM to free GPU memory...[/dim]")
            llm_provider.unload_model()
    except ImportError:
        pass
    
    try:
        import torch
        from diffusers import ZImagePipeline
    except ImportError:
        raise ImportError(
            "Local mode requires diffusers and torch. "
            "Install with: pip install pyros-cli[local]\n"
            "Note: diffusers must be installed from source for Z-Image support:\n"
            "pip install git+https://github.com/huggingface/diffusers"
        )
    
    model_path = _get_model_path()
    console.print(f"[cyan]Loading Z-Image-Turbo from: {model_path}[/cyan]")
    
    _pipeline = ZImagePipeline.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
    )
    
    # Move to GPU if available
    if torch.cuda.is_available():
        _pipeline.to("cuda")
        console.print(f"[green]✓ Z-Image-Turbo loaded on CUDA[/green]")
    else:
        console.print("[yellow]⚠ CUDA not available, using CPU (will be slow)[/yellow]")
        _pipeline.to("cpu")
    
    return _pipeline


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_steps: int = 9,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, Image.Image], None]] = None,
) -> tuple[Image.Image, str]:
    """Generate an image using Z-Image-Turbo.
    
    Args:
        prompt: The text prompt for image generation
        width: Output image width (default 1024)
        height: Output image height (default 1024)
        num_steps: Number of inference steps (default 9, actually 8 DiT forwards)
        seed: Random seed for reproducibility (None for random)
        output_path: Custom output path (auto-generated if None)
        progress_callback: Optional callback(step, total, latent_preview)
        
    Returns:
        Tuple of (PIL Image, output file path)
    """
    import torch
    
    pipe = _load_pipeline()
    
    # Set up generator with seed
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()
    generator = torch.Generator(device).manual_seed(seed)
    
    console.print(f"[dim]Seed: {seed}[/dim]")
    console.print(f"[cyan]Generating {width}x{height} image...[/cyan]")
    
    # Generate image
    # Note: Z-Image-Turbo uses guidance_scale=0.0 (it's distilled)
    result = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_inference_steps=num_steps,
        guidance_scale=0.0,  # Must be 0 for Turbo model
        generator=generator,
    )
    
    image = result.images[0]
    
    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = _get_output_dir()
        output_path = str(output_dir / f"zimage_{timestamp}_{seed}.png")
    
    # Save image
    image.save(output_path)
    console.print(f"[green]✓ Image saved to: {output_path}[/green]")
    
    return image, output_path


def generate_image_with_preview(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_steps: int = 9,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
) -> tuple[Image.Image, str]:
    """Generate an image with Rich live preview in terminal.
    
    Same as generate_image but shows progress in terminal.
    """
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    
    import torch
    
    pipe = _load_pipeline()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()
    generator = torch.Generator(device).manual_seed(seed)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Generating image (seed: {seed})...", total=num_steps)
        
        def callback(pipe, step, timestep, callback_kwargs):
            progress.update(task, completed=step + 1)
            return callback_kwargs
        
        result = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=num_steps,
            guidance_scale=0.0,
            generator=generator,
            callback_on_step_end=callback,
        )
    
    image = result.images[0]
    
    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = _get_output_dir()
        output_path = str(output_dir / f"zimage_{timestamp}_{seed}.png")
    
    image.save(output_path)
    console.print(f"[green]✓ Image saved to: {output_path}[/green]")
    
    return image, output_path


def unload_pipeline():
    """Unload the pipeline to free GPU memory."""
    global _pipeline
    
    if _pipeline is not None:
        import gc
        import torch
        
        del _pipeline
        _pipeline = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        console.print("[dim]Z-Image pipeline unloaded[/dim]")


def get_gpu_memory_info() -> dict:
    """Get GPU memory information."""
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            return {
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "free_gb": round(total - reserved, 2),
            }
    except Exception:
        pass
    return {"error": "CUDA not available"}

