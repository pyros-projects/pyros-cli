"""Local LLM provider using Qwen3-4B for text generation.

This module provides a local alternative to cloud LLMs for:
- Prompt enhancement
- Prompt variable generation
"""

import json
import os
from typing import Optional

from rich.console import Console

console = Console()

# Lazy imports to avoid loading heavy libraries unless needed
_model = None
_tokenizer = None


def _get_model_path() -> str:
    """Get the local LLM model path from env or use HuggingFace default."""
    return os.getenv("QWEN_4B_PATH", "Qwen/Qwen3-4B-Instruct-2507")


def _load_model():
    """Lazy load the model and tokenizer.
    
    Automatically unloads the image generator to free GPU memory,
    since both models cannot fit in VRAM simultaneously.
    """
    global _model, _tokenizer
    
    if _model is not None:
        return _model, _tokenizer
    
    # Unload image generator first to free GPU memory
    try:
        from pyros_cli.local import image_generator
        if image_generator._pipeline is not None:
            console.print("[dim]Unloading image model to free GPU memory...[/dim]")
            image_generator.unload_pipeline()
    except ImportError:
        pass
    
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        raise ImportError(
            "Local mode requires transformers and torch. "
            "Install with: pip install pyros-cli[local]"
        )
    
    model_path = _get_model_path()
    console.print(f"[cyan]Loading local LLM from: {model_path}[/cyan]")
    
    _tokenizer = AutoTokenizer.from_pretrained(model_path)
    _model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    
    console.print("[green]✓ Local LLM loaded successfully[/green]")
    return _model, _tokenizer


def generate_text(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.8,
) -> str:
    """Generate text using the local LLM.
    
    Args:
        prompt: The user prompt/instruction
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        
    Returns:
        Generated text response
    """
    import torch
    
    model, tokenizer = _load_model()
    
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1]:], 
        skip_special_tokens=True
    )
    return response.strip()


def enhance_prompt(user_prompt: str, instruction: str = "") -> str:
    """Enhance a prompt for better image generation.
    
    Args:
        user_prompt: The original user prompt
        instruction: Optional enhancement instructions
        
    Returns:
        Enhanced prompt optimized for image generation
    """
    system_prompt = """You are an expert prompt engineer for image generation models.
Your task is to enhance the user's prompt to create more detailed, vivid, and visually 
compelling descriptions that will produce stunning images.

Rules:
- Add specific details about lighting, atmosphere, style, and composition
- Maintain the core intent of the original prompt
- Keep the enhanced prompt concise but descriptive
- Output ONLY the enhanced prompt, nothing else"""

    full_prompt = f"""{system_prompt}

Original prompt: {user_prompt}
{f'Additional instructions: {instruction}' if instruction else ''}

Enhanced prompt:"""

    return generate_text(full_prompt, max_tokens=1024, temperature=0.7)


def generate_prompt_variable_values(
    variable_name: str, 
    context_prompt: str,
    count: int = 20
) -> list[str]:
    """Generate values for a prompt variable using local LLM.
    
    Args:
        variable_name: Name of the variable (e.g., 'cat_breed')
        context_prompt: The full prompt for context
        count: Number of values to generate (minimum)
        
    Returns:
        List of generated values
    """
    # Detect if this is asking for full scene descriptions vs simple values
    # Patterns that indicate full scene/prompt generation:
    #   - "variations_of_X", "scene_of_X", "scenes_X"
    #   - "prompt_X", "prompts_X", "description_of_X"
    # Patterns that indicate simple values (NOT full scenes):
    #   - "X_style", "X_color", "X_type" (these want style/color/type VALUES)
    var_lower = variable_name.lower()
    
    # Check for prefix patterns that want full descriptions
    full_description_prefixes = ['variation', 'scene', 'description', 'prompt', 'version']
    is_variation_request = any(var_lower.startswith(prefix) or f'_{prefix}' in var_lower or f'{prefix}_of' in var_lower
                               for prefix in full_description_prefixes)
    
    # Override: if it ends with common suffix patterns, it wants VALUES not descriptions
    value_suffixes = ['_style', '_color', '_type', '_mood', '_artist', '_genre', '_setting']
    if any(var_lower.endswith(suffix) for suffix in value_suffixes):
        is_variation_request = False
    
    if is_variation_request:
        prompt = f"""Generate {count} diverse, creative COMPLETE SCENE DESCRIPTIONS for use in image generation.

The variable name "{variable_name}" suggests you should create full, detailed scene descriptions.
Context prompt: "{context_prompt}"

Requirements:
- Each value should be a COMPLETE, standalone image generation prompt
- Include rich visual details: lighting, atmosphere, composition, style
- Make each variation distinctly different from the others
- Values should be 1-3 sentences each, painting a vivid picture
- Return ONLY a valid JSON array of strings

Example for "variations_of_a_cat":
["A fluffy orange tabby cat lounging on a sunlit windowsill, golden afternoon light streaming through lace curtains", "A sleek black cat perched on ancient library books, mysterious candlelight casting dramatic shadows", "A playful calico kitten mid-pounce in a field of wildflowers, soft bokeh background"]

JSON array:"""
    else:
        prompt = f"""Generate a list of {count} diverse values for the variable "{variable_name}".

This variable will be substituted into this image generation prompt: "{context_prompt}"
The variable __{variable_name}__ should be REPLACED by each value you generate.

Requirements:
- Values should be specific nouns, adjectives, or short phrases
- Include both common and unique/interesting options  
- Each value should grammatically fit when substituted into the prompt
- Return ONLY a valid JSON array of strings

Examples:
- For "cat_breed": ["Persian", "Siamese", "Maine Coon", "Bengal"]
- For "art_style": ["impressionist", "cyberpunk", "watercolor", "art nouveau"]
- For "emotion": ["joyful", "melancholic", "serene", "fierce"]

JSON array:"""

    response = generate_text(prompt, max_tokens=4096, temperature=0.8)
    
    # Try to extract JSON array from response
    try:
        # Find JSON array in response
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            values = json.loads(json_str)
            if isinstance(values, list) and len(values) >= count:
                return values[:count + 10]  # Return a few extra
    except json.JSONDecodeError:
        pass
    
    # Fallback: try to parse line by line
    console.print("[yellow]Warning: Could not parse JSON, attempting line parsing[/yellow]")
    lines = [line.strip().strip('"').strip("'").strip(',') 
             for line in response.split('\n') 
             if line.strip() and not line.strip().startswith('[') and not line.strip().startswith(']')]
    
    if len(lines) >= count // 2:
        return lines
    
    # Last resort: return empty and let caller handle
    console.print("[red]Warning: Failed to generate prompt variable values[/red]")
    return []


def unload_model():
    """Unload the model to free GPU memory."""
    global _model, _tokenizer
    
    if _model is not None:
        import gc
        import torch
        
        del _model
        del _tokenizer
        _model = None
        _tokenizer = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        console.print("[dim]LLM model unloaded[/dim]")

