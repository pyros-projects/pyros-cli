import questionary
from rich.console import Console
from rich.table import Table
from rich.text import Text
from datetime import datetime
import os

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.models.user_messages import UserMessages, HistoryItem

console = Console()

class HistoryCommand(BaseCommand):
    """Command to view and select from message history"""
    
    name = "/history"
    help_text = "View and select from history: /history [base-prompt|eval-prompt|command]"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """Display and select items from message history"""
        # Load user messages from file
        user_messages = UserMessages.load_from_file()
        
        # Get the history from user_messages
        history = user_messages.get_history()
        
        if not history:
            console.print("History is empty.", style="yellow")
            return CommandResult(is_command=True, should_generate=False)
        
        # Filter by type if args provided
        filter_type = None
        if args:
            arg_type = args.strip().lower()
            if arg_type == "base-prompt":
                filter_type = "base_prompt"
            elif arg_type == "eval-prompt" or arg_type == "evaluated-prompt":
                filter_type = "evaluated_prompt"
            elif arg_type == "command":
                filter_type = "command"
            else:
                console.print(f"Unknown history type: {arg_type}", style="yellow")
                console.print("Available types: base-prompt, eval-prompt, command", style="yellow")
                return CommandResult(is_command=True, should_generate=False)
        
        # Filter the history if needed
        filtered_history = history
        if filter_type:
            filtered_history = [item for item in history if item.type == filter_type]
            if not filtered_history:
                console.print(f"No history items of type '{filter_type}' found.", style="yellow")
                return CommandResult(is_command=True, should_generate=False)
        
        # Display history in a table
        table = Table(title="Message History")
        table.add_column("Time", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Message", style="white")
        
        # Add rows to the table, newest first
        for item in reversed(filtered_history):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(item.timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = item.timestamp
            
            # Format message for display (truncate if too long)
            message = item.message
            if len(message) > 50:
                message = message[:47] + "..."
            
            # Format type for display
            type_display = item.type.replace("_", " ").title()
            
            table.add_row(time_str, type_display, message)
        
        console.print(table)
        
        # Create choices for the selection menu
        choices = []
        for i, item in enumerate(filtered_history):
            message = item.message
            if len(message) > 40:
                message = message[:37] + "..."
            
            try:
                dt = datetime.fromisoformat(item.timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = item.timestamp
                
            type_display = item.type.replace("_", " ").title()
            choice_text = f"[{time_str}] {type_display}: {message}"
            choices.append(questionary.Choice(choice_text, value=i))
        
        # Add option to cancel
        choices.append(questionary.Choice("Cancel", value="cancel"))
        
        # Let user select an item from history
        selected = await questionary.select(
            "Select a history item to use as current prompt:",
            choices=choices
        ).ask_async()
        
        if selected == "cancel":
            return CommandResult(is_command=True, should_generate=False)
        
        selected_item = filtered_history[selected]
        
        # Confirm using the selected item
        confirmed = await questionary.confirm(
            f"Set current prompt to: {selected_item.message[:50]}{'...' if len(selected_item.message) > 50 else ''}",
            default=True
        ).ask_async()
        
        if not confirmed:
            return CommandResult(is_command=True, should_generate=False)
            
        # Set the selected message as the current prompt
        if selected_item.type == "base_prompt" or selected_item.type == "evaluated_prompt":
            user_messages.set_base_prompt(selected_item.message)
            console.print("Base prompt updated.", style="green")
            # Use the dedicated flag to reset regenerate mode and return to prompt input
            return CommandResult(
                is_command=True, 
                should_generate=False, 
                should_continue=False,
                should_reset_regenerate=True
            )
        else:  # Command
            console.print("Command added to prompt.", style="green")
            return CommandResult(
                is_command=True, 
                should_generate=False, 
                should_continue=False,
                should_reset_regenerate=True
            ) 