from typing import Any, Optional, Dict

class CommandResult:
    """Result of command processing"""
    def __init__(self, 
                 is_command: bool = False, 
                 should_continue: bool = True,
                 should_generate: bool = True,
                 should_reset_regenerate: bool = False,
                 data: Any = None):
        self.is_command = is_command  # Was the input a command
        self.should_continue = should_continue  # Should the main loop continue
        self.should_generate = should_generate  # Should image generation proceed
        self.should_reset_regenerate = should_reset_regenerate  # Should reset regenerate mode and return to prompt input
        self.data = data  # Any data to return from command

class BaseCommand:
    """Base class for all commands"""
    
    name: str = ""  # Command name (e.g., "/help")
    help_text: str = ""  # Help text for the command
    
    def __init__(self, command_registry: Optional[Dict[str, 'BaseCommand']] = None):
        """
        Initialize the command
        
        Args:
            command_registry: Optional reference to the command registry
        """
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """
        Execute the command with the given arguments
        
        Args:
            args: String arguments passed to the command
            
        Returns:
            CommandResult: The result of command execution
        """
        raise NotImplementedError("Command execution not implemented") 