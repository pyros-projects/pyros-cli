from rich.console import Console
import uuid

from pyros_cli.services.commands.base_command import BaseCommand, CommandResult
from pyros_cli.models.user_messages import WorkflowProperty

console = Console()

class CntrlCommand(BaseCommand):
    """Command to control ComfyUI nodes"""
    
    name = "/cntrl"
    help_text = "Control ComfyUI nodes with format: /cntrl <node_id> <property> <value>"
    
    def __init__(self, command_registry=None):
        self.command_registry = command_registry
    
    async def execute(self, args: str) -> CommandResult:
        """Control ComfyUI nodes by setting node properties"""
        if not args:
            console.print("Usage: /cntrl <node_id> <property> <value>", style="yellow")
            return CommandResult(is_command=True, should_generate=False)
            
        # Parse the arguments
        arg_parts = args.strip().split(' ', 2)
        
        if len(arg_parts) < 3:
            if len(arg_parts) == 1 and arg_parts[0].strip() == "clear":
                return CommandResult(is_command=True, should_generate=False, data="cntrl-clear")
            console.print("Not enough arguments. Usage: /cntrl <node_id> <property> <value>", style="yellow")
            return CommandResult(is_command=True, should_generate=False)
            
        node_id = arg_parts[0].strip()
        node_property = arg_parts[1].strip()
        value = arg_parts[2].strip()
        
        # Generate a unique call_id for this property change
        call_id = str(uuid.uuid4())
        
        # Create a WorkflowProperty object
        workflow_property = WorkflowProperty(
            node_id=node_id,
            node_property=node_property,
            value=value,
            alias=call_id
        )
        
        console.print(f"[bold green]Setting workflow property:[/] Node: {node_id}, Property: {node_property}, Value: {value}")
        
        # Return the workflow property in the data field
        return CommandResult(
            is_command=True, 
            should_generate=True,
            data=workflow_property
        ) 