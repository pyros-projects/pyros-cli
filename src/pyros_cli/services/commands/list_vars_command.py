import random
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.models.prompt_vars import load_prompt_vars
from flock.cli.utils import print_subheader

console = Console()

class ListVarsCommand(BaseCommand):
    """Command to list prompt variables"""
    
    name = "/list-vars"
    help_text = "List all available prompt variables"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """List all available prompt variables"""
        prompt_vars = load_prompt_vars()
        
        if not prompt_vars:
            console.print("No prompt variables found.", style="yellow")
            return CommandResult(is_command=True, should_generate=False)
            
        choices = [
            f"{var.prompt_id} - {var.description[:50] + '...' if var.description and len(var.description) > 50 else var.description or 'No description'}\n"
            for var in prompt_vars.values()
        ]
        
        selected = await questionary.select(
            "Select a prompt variable to view:",
            choices=choices
        ).ask_async()
        
        if not selected:
            return CommandResult(is_command=True, should_generate=False)
            
        # Extract the prompt_id from the selection
        prompt_id = selected.split(" - ")[0]
        
        if prompt_id in prompt_vars:
            var = prompt_vars[prompt_id]
            print_subheader(f"[bold cyan]Prompt Variable:[/] {var.prompt_id}")

            console.line()
            
            if var.description:
                console.print(f"[bold cyan]Description:[/] {var.description}")
                
            console.print(f"[bold cyan]File Path:[/] {var.file_path}")
            
            # Show usage examples
            base_var_name = var.prompt_id
            example_random = f"A prompt with {base_var_name}"
            
            console.line()
            console.print("[bold cyan]Usage Examples:[/]")
            console.print(f"  Random value: {base_var_name}")
            
            # Only show indexed example if values exist
            if var.values and len(var.values) > 0:
                example_index = 0  # Use first index for example
                console.print(f"  Specific value: {base_var_name.replace('__', '__')}:{example_index}__")
            
            console.line()
            if var.values:
                total_values = len(var.values)
                console.print(f"[bold cyan]Values[/] ({total_values} total):")
                
                # Determine how many values to show
                if total_values <= 10:
                    # Show all values if there are 10 or fewer
                    indices_to_show = list(range(total_values))
                else:
                    # Show first 5 and last 5 with a gap in between for longer lists
                    indices_to_show = list(range(5)) + list(range(total_values - 5, total_values))
                
                # Display the values with their indices
                for idx in indices_to_show:
                    if idx == 5 and total_values > 10:
                        console.print(f"  [...{total_values - 10} more values...]")
                    else:
                        console.print(f"  [cyan]{idx}.[/] {var.values[idx]}")
                
                # Show how to use with specific index
                console.line()
                console.print(f"[dim]Use [yellow]{base_var_name.replace('__', '__')}:N__[/dim] [dim]to access a specific index (0-{total_values-1})[/dim]")
            else:
                console.print("[yellow]No values found.[/]")
                
        return CommandResult(is_command=True, should_generate=False) 