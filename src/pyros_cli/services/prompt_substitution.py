import asyncio
import random
import re
from rich.console import Console

from pyros_cli.models.prompt_vars import load_prompt_vars, save_prompt_var

console = Console()


async def generate_missing_prompt_var(variable_name: str, full_prompt: str) -> list[str] | None:
    """Generate values for a missing prompt variable using AI.
    
    Args:
        variable_name: The variable name without underscores (e.g., 'cat_race')
        full_prompt: The complete prompt for context
        
    Returns:
        List of generated values, or None if generation failed
    """
    # Import here to avoid circular imports
    from flock import Flock
    from pyros_cli.agents.prompt_var_generator_agent import register_prompt_var_generator_agent
    from pyros_cli.models.flock_artifacts import (
        PromptVarGenerationRequest,
        GeneratedPromptVar,
    )
    from pyros_cli.services.config import load_config
    
    config = load_config()
    if not config.model_name:
        console.print("[yellow]Warning: No AI model configured. Cannot generate prompt variable.[/yellow]")
        return None
    
    console.print(f"\n[bold cyan]🤖 Generating values for missing variable: __{variable_name}__[/bold cyan]")
    console.print(f"[dim]Using AI to create ~20 values based on prompt context...[/dim]\n")
    
    try:
        flock = Flock(model=config.model_name)
        register_prompt_var_generator_agent(flock)
        
        # Publish the generation request
        request = PromptVarGenerationRequest(
            variable_name=variable_name,
            full_prompt=full_prompt
        )
        await flock.publish(request)
        await flock.run_until_idle()
        
        # Get the result
        results = await flock.store.get_by_type(GeneratedPromptVar)
        if results:
            generated = results[0]
            
            # Save to disk
            file_path = save_prompt_var(
                variable_name=variable_name,
                description=generated.description,
                values=generated.values
            )
            
            console.print(f"[green]✓ Generated {len(generated.values)} values for __{variable_name}__[/green]")
            console.print(f"[dim]Saved to: {file_path}[/dim]\n")
            
            return generated.values
        else:
            console.print("[red]✗ Failed to generate values - no result from AI[/red]")
            return None
            
    except Exception as e:
        console.print(f"[red]✗ Error generating prompt variable: {e}[/red]")
        return None


def _run_async(coro):
    """Run an async coroutine synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

def substitute_prompt_vars(prompt: str, auto_generate: bool = True) -> str:
    """
    Substitute prompt variables in the format __varname__ with random values
    from the corresponding prompt variable collection.
    
    Also supports __varname:123__ format to use the value at a specific index.
    
    If a variable doesn't exist and auto_generate is True, uses AI to generate
    values and saves them for future use.
    
    Args:
        prompt: The user prompt text
        auto_generate: If True, generate missing variables using AI
        
    Returns:
        The prompt with all variables substituted
    """
    # Load all prompt variables
    prompt_vars = load_prompt_vars()
    
    # Pattern to find __variable__ or __variable:index__ in the prompt
    # Updated to include slashes for subfolder paths and optional index specification
    pattern = r'(__[a-zA-Z0-9_\-/]+(?::\d+)?__)'
    
    # Keep substituting until no more matches are found
    substituted_prompt = prompt
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        matches = re.findall(pattern, substituted_prompt)
        
        if not matches:
            # No more variables to substitute
            break
            
        # Track if we made any substitutions in this iteration
        made_substitution = False
        
        for match in matches:
            # Check if this is an indexed variable reference
            if ":" in match:
                # Parse the variable name and index
                var_parts = match.split(":")
                var_name = var_parts[0] + "__"  # Add back the closing underscores
                # Extract index and remove trailing "__"
                index_str = var_parts[1].rstrip("_")
                try:
                    index = int(index_str)
                except ValueError:
                    # Invalid index format, skip this variable
                    continue
                
                # Find the base variable (or generate if missing)
                if var_name not in prompt_vars and auto_generate:
                    # Extract the raw variable name (without underscores)
                    raw_var_name = var_name.strip("_")
                    generated_values = _run_async(
                        generate_missing_prompt_var(raw_var_name, prompt)
                    )
                    if generated_values:
                        # Reload prompt vars to include the newly generated one
                        prompt_vars = load_prompt_vars()
                
                if var_name in prompt_vars:
                    var = prompt_vars[var_name]
                    if var.values:
                        if 0 <= index < len(var.values):
                            # Use the value at the specified index
                            replacement = var.values[index]
                            # Replace the variable with the indexed value
                            substituted_prompt = substituted_prompt.replace(match, replacement, 1)
                            made_substitution = True
                            # Log the substitution
                            console.print(f"[dim]Substituted {match} with value at index {index}: {replacement}[/dim]")
                        else:
                            # Index out of range
                            console.print(f"[yellow]Warning: Index {index} out of range for {var_name} (has {len(var.values)} values)[/yellow]")
            else:
                # Regular variable without index
                var_name = match
                
                # Check if variable exists, if not try to generate it
                if var_name not in prompt_vars and auto_generate:
                    # Extract the raw variable name (without underscores)
                    raw_var_name = var_name.strip("_")
                    generated_values = _run_async(
                        generate_missing_prompt_var(raw_var_name, prompt)
                    )
                    if generated_values:
                        # Reload prompt vars to include the newly generated one
                        prompt_vars = load_prompt_vars()
                
                if var_name in prompt_vars:
                    var = prompt_vars[var_name]
                    if var.values:
                        # Select a random value from the variable's values
                        replacement = random.choice(var.values)
                        
                        # Replace the variable with the random value
                        substituted_prompt = substituted_prompt.replace(var_name, replacement, 1)
                        made_substitution = True
                        
                        # Log the substitution
                        console.print(f"[dim]Substituted {var_name} with random value: {replacement}[/dim]")
                else:
                    # Variable still doesn't exist after generation attempt
                    console.print(f"[yellow]Warning: Unknown variable {var_name} - leaving as-is[/yellow]")
            
        # If we didn't make any substitutions in this iteration, break
        # (This handles cases where variable names don't match any prompt vars)
        if not made_substitution:
            break
    
    return substituted_prompt