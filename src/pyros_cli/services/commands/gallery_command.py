import random
import questionary
from rich.console import Console

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.models.prompt_vars import load_prompt_vars
from flock.cli.utils import print_subheader

from pyros_cli.services.gallery import show_gallery

console = Console()

class GalleryCommand(BaseCommand):
    """Command to list prompt variables"""
    
    name = "/gallery"
    help_text = "Show the gallery"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """Show the gallery"""
        show_gallery()
        
                
        return CommandResult(is_command=True, should_generate=False) 