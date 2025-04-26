from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult

console = Console()

class HelpCommand(BaseCommand):
    """Help command to display available commands"""
    
    name = "/help"
    help_text = "Display available commands"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """Display help for available commands"""
        # Display commands table
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        
        if self.command_registry:
            for cmd_name, cmd_instance in sorted(self.command_registry.items()):
                table.add_row(cmd_name, cmd_instance.help_text)
                
        console.print(table)
        
        # Display variable syntax information
        var_help = Text()
        var_help.append("Variable Syntax:\n", style="bold cyan")
        var_help.append("  __variable__      ", style="yellow")
        var_help.append("Use a random value from the variable\n")
        var_help.append("  __variable:123__  ", style="yellow")
        var_help.append("Use the specific value at index 123\n")
        var_help.append("\nUse ", style="dim")
        var_help.append("/list-vars", style="cyan")
        var_help.append(" to see all available variables and their indices", style="dim")
        
        console.print(Panel(var_help, title="Prompt Variables", border_style="green"))
        
        return CommandResult(is_command=True, should_generate=False) 