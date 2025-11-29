import random
import questionary
from rich.console import Console

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.models.prompt_vars import load_prompt_vars
from pyros_cli.utils.cli_helper import print_subheader

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
        print_subheader("Opening Gallery")
        gallery_url = show_gallery()
        console.print(f"Gallery is now running at [link={gallery_url}]{gallery_url}[/link]")
        console.print("A browser window should open automatically. You can continue using Pyros CLI.")
        console.print("Close the browser when you're done viewing the gallery.")
                
        return CommandResult(is_command=True, should_generate=False) 