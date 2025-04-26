import random
import re
from rich.console import Console

from pyros_cli.models.prompt_vars import load_prompt_vars

console = Console()

def substitute_prompt_vars(prompt: str) -> str:
    """
    Substitute prompt variables in the format __varname__ with random values
    from the corresponding prompt variable collection.
    
    Also supports __varname:123__ format to use the value at a specific index.
    
    Args:
        prompt: The user prompt text
        
    Returns:
        The prompt with all variables substituted
    """
    # Load all prompt variables
    prompt_vars = load_prompt_vars()
    if not prompt_vars:
        # No prompt vars available, return original prompt
        return prompt
    
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
                
                # Find the base variable
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
            
        # If we didn't make any substitutions in this iteration, break
        # (This handles cases where variable names don't match any prompt vars)
        if not made_substitution:
            break
    
    return substituted_prompt 