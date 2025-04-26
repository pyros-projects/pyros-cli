import os
import importlib
import inspect
from typing import Dict, Type
from rich.console import Console

from pyros_cli.agents.flock_handler import create_flock
from pyros_cli.globals import CURRENT_DIR
from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.services.commands.configure_ai_command import ConfigureAiCommand
from pyros_cli.services.commands.gallery_command import GalleryCommand
from pyros_cli.services.commands.help_command import HelpCommand
from pyros_cli.services.commands.list_vars_command import ListVarsCommand
from pyros_cli.services.commands.cntrl_command import CntrlCommand
from pyros_cli.services.commands.history_command import HistoryCommand
from pyros_cli.services.config import load_config
from pyros_cli.services.prompt_substitution import substitute_prompt_vars
from pyros_cli.models.user_messages import WorkflowProperty

console = Console()

class CommandRegistry:
    """Registry for all available commands"""
    
    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}
        self.load_default_commands()
        
    def register_command(self, command_class: Type[BaseCommand]):
        """Register a command class"""
        command = command_class(command_registry=self.commands)
        self.commands[command.name] = command
        
    def load_default_commands(self):
        """Load the default built-in commands"""
        self.register_command(HelpCommand)
        self.register_command(ListVarsCommand)
        self.register_command(CntrlCommand)
        self.register_command(ConfigureAiCommand)
        self.register_command(GalleryCommand)
        self.register_command(HistoryCommand)

    def load_commands_from_directory(self, directory="services/commands"):
        """Load commands from the commands directory"""
        # Skip these files when scanning for commands
        skip_files = ["__init__.py", "base_command.py", "help_command.py", "list_vars_command.py"]

        # Get the absolute path to the commands directory
        commands_dir = os.path.abspath(os.path.join(CURRENT_DIR, directory))
        
        for filename in os.listdir(commands_dir):
            if filename.endswith(".py") and filename not in skip_files:
                module_name = filename[:-3]  # Remove .py extension
                module_path = f"pyros_cli.services.commands.{module_name}"
                
                try:
                    module = importlib.import_module(module_path)
                    
                    # Find command classes in the module
                    for _, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseCommand) and 
                            obj is not BaseCommand):
                            self.register_command(obj)
                except Exception as e:
                    console.print(f"Error loading command module {module_path}: {e}", style="red")
        
    async def evaluate(self, user_input: str) -> CommandResult:
        """Evaluate user input to check if it's a command or plain text"""
        console.line()
        if not user_input:
            return CommandResult(is_command=False)
            
        if user_input.startswith("/"):
            # This is a command
            command_parts = user_input.split(" ", 1)
            command = command_parts[0].lower()
            args = command_parts[1] if len(command_parts) > 1 else ""
            
            if command in self.commands:
                cmd_instance = self.commands[command]
                result = await cmd_instance.execute(args)
                console.line()
                
                # Check if the result contains a WorkflowProperty
                if isinstance(result.data, WorkflowProperty):
                    # Return the result with the WorkflowProperty
                    return result
                    
                return result
            else:
                console.print(f"Unknown command: {command}", style="red")
                console.line()
                return CommandResult(is_command=True, should_generate=False)

        console.line()    
        # Not a command, process prompt variables
        config = load_config()
        if config.ai_provider and ">" in user_input:
            user_input = evaluate_agents(user_input)
        processed_prompt = substitute_prompt_vars(user_input)
        
        # If the prompt was modified, return it in the data field
        if processed_prompt != user_input:
            console.print(f"[bold green]Final prompt:[/] {processed_prompt}")
            return CommandResult(is_command=False, should_generate=True, data=processed_prompt)
            
        # No substitutions needed, continue with regular prompt flow
        return CommandResult(is_command=False)

def evaluate_agents(user_input: str):
    """Evaluate AI agents"""
    prompt = user_input.split(">")[0].strip()
    agent_instruction = user_input.split(">")[1].strip()
    prompt, agent_instruction = create_flock(prompt, agent_instruction)
    return prompt, agent_instruction


# Function to evaluate a user prompt
async def evaluate_prompt(user_input: str) -> CommandResult:
    """
    Evaluate user input to determine if it's a command
    Returns CommandResult with processing information
    """
    registry = CommandRegistry()
    # Load any additional commands from directory
    registry.load_commands_from_directory()
    return await registry.evaluate(user_input)
