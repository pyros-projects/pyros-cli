# Commands and Variables Reference

## Overview
Pyros CLI provides a powerful system of commands and variables that can be used within prompts to control generation parameters, modify workflows, and access dynamic content.

## Command System Architecture

### Command Structure
All commands in Pyros CLI implement the `BaseCommand` abstract class with:
- `name`: The command identifier with slash prefix (e.g., "/help")
- `help_text`: Description of the command's purpose
- `execute(args)`: Async method that implements the command functionality

### Command Result
Commands return a `CommandResult` object with:
- `is_command`: Indicates if input was processed as a command
- `should_continue`: Controls whether the main loop should continue
- `should_generate`: Controls whether image generation should proceed
- `data`: Optional data returned by the command (workflow properties, text, etc.)

### Command Registry
- Commands are dynamically discovered and registered in the `CommandRegistry` class
- The registry maintains a dictionary of command instances
- Command help information is automatically generated from registered commands

## Available Commands

### Information Commands

#### `/help`
**Description**: Display a table of all available commands  
**Implementation**: The `HelpCommand` class displays a rich table with all commands and their descriptions
**Usage**: `/help`  
**Output**: Table showing all commands and descriptions  
**Affects Generation**: No  

#### `/list-vars`
**Description**: List all available prompt variables  
**Implementation**: The `ListVarsCommand` class shows an interactive selector to browse variables
**Usage**: `/list-vars`  
**Output**: 
1. Interactive selector with variable names and descriptions
2. When a variable is selected, shows details including:
   - Description
   - File path
   - Sample values (up to 5 random samples)
**Affects Generation**: No  

### Workflow Control Commands

#### `/cntrl`
**Description**: Control ComfyUI nodes by modifying properties  
**Implementation**: The `CntrlCommand` class creates a `WorkflowProperty` object that is applied to the workflow
**Usage**: `/cntrl <node_id> <property> <value>`  
**Examples**:
- `/cntrl 3 cfg 7.5` - Set the CFG value in node 3
- `/cntrl 5 width 768` - Set the width property in node 5
- `/cntrl 10 steps 30` - Set sampling steps in node 10
**Affects Generation**: Yes - modifies workflow before sending to ComfyUI  

### AI Integration Commands

#### `/configure-ai`
**Description**: Configure AI provider for prompt enhancement  
**Implementation**: The `ConfigureAiCommand` class sets up AI integration with different providers
**Usage**: `/configure-ai <provider>`  
**Supported Providers**:
- `ollama`: Local models via Ollama
- `openai`: OpenAI models (GPT-4, etc.)
- `anthropic`: Anthropic models (Claude)
- `groq`: Groq API for fast inference
- `gemini`: Google's Gemini models
**Process**:
1. Prompts for provider-specific information (model name, API keys)
2. Stores configuration in .env file
3. Tests connection to provider
**Affects Generation**: No - configures AI but doesn't affect current generation  

### System Commands

#### `/gallery`
**Description**: Open the image gallery  
**Implementation**: The `GalleryCommand` class invokes the gallery viewer
**Usage**: `/gallery`  
**Output**: Opens the gallery interface to browse generated images  
**Affects Generation**: No  

## Creating Custom Commands

New commands can be created by:
1. Creating a new Python file in the `commands` directory
2. Implementing the `BaseCommand` class
3. Setting the `name` and `help_text` class attributes
4. Implementing the `execute(args)` method

Example template:
```python
from pyros_cli.services.commands.base_command import BaseCommand, CommandResult

class MyCustomCommand(BaseCommand):
    name = "/my-command"
    help_text = "Description of what my command does"
    
    async def execute(self, args: str) -> CommandResult:
        # Command implementation here
        return CommandResult(
            is_command=True,
            should_generate=True,  # Whether to proceed with generation
            data=None  # Optional data to return
        )
```

## Command Processing Flow

1. User input is sent to `evaluate_prompt()` function
2. The function checks if the input starts with a command character (/)
3. If so, it extracts the command name and arguments
4. It looks up the command in the registry and executes it
5. The command returns a `CommandResult` indicating what to do next
6. Based on the result, the system either:
   - Continues with generation
   - Skips generation
   - Exits the application
   - Modifies the workflow with the command's data

## Variable System

### Variable Format and Implementation
Variables use the `__variable_name__` format with double underscores on both sides.

### Variable File Format
Variables are stored as text files with each line representing a possible value:
```
Value 1
Value 2
Value 3
```

### Accessing Variable Information
The `/list-vars` command provides detailed information about available variables:
- Variable ID (with double underscores)
- Description (if available)
- File path
- Sample values

### Variable Categories

#### System Variables
| Variable | Description | Example Value |
|----------|-------------|---------------|
| `__date__` | Current date | "2023-04-18" |
| `__time__` | Current time | "14:30:22" |
| `__datetime__` | Date and time | "2023-04-18 14:30:22" |
| `__random__` | Random number | "42" |
| `__seed__` | Current seed value | "1234567890" |

#### Collection Variables
When a collection variable is referenced, a random item is selected:
```
A __colors__ flower in a garden  # colors might resolve to "red", "blue", etc.
```

### Variable Selection Syntax
- `__variable__` - Uses a random value from the variable
- `__variable:123__` - Uses the specific entry at index 123 in the variable file

## Integration Example
A complex prompt using both commands and variables:

```
/cntrl 10 steps 40 /cntrl 3 cfg 8.5
A fantasy landscape with __style__, featuring a __time_of_day__ sky and __weather_condition__
```

This would:
1. Set workflow parameters for steps (node 10) and CFG (node 3)
2. Replace variables with random values from their respective files
3. Send the resulting text to ComfyUI for generation 