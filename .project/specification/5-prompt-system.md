# Prompt System

## Overview
The prompt system is a core component of Pyros CLI that provides a rich environment for crafting text prompts for image generation. It includes variable substitution, command processing, prompt evaluation, and history management.

## Prompt Types

### Base Prompt
- The raw text entered by the user
- May contain variables (with `__` prefix and suffix) and commands (with `/` prefix)
- Stored in session history for reuse

### Evaluated Prompt
- The result after processing the base prompt
- Variables are replaced with their values
- Commands are processed and may modify the prompt
- This is the actual text sent to ComfyUI

## Variable System

### Variable Implementation
Variables are implemented in the `prompt_vars.py` module:
```python
class PromptVars(BaseModel):
    file_path: Optional[str] = None
    prompt_id: Optional[str] = None
    description: Optional[str] = None
    values: list[str] = []
```

### Variable Loading
Variables are loaded from text or markdown files in the `library/prompt_vars` directory:
```python
def load_prompt_vars() -> dict[str, PromptVars]:
    # Get the absolute path to the prompt_vars directory
    prompt_vars_dir = os.path.join(CURRENT_DIR, "library/prompt_vars")
    
    # Walk through all directories and subdirectories
    for root, _, files in os.walk(prompt_vars_dir):
        for file in files:
            # Check for both .md and .txt files
            if file.endswith((".md", ".txt")):
                # Process file and create PromptVars object
```

Key aspects of variable loading:
- Recursively scans the `library/prompt_vars` directory
- Supports both .txt and .md file formats
- Handles files in subdirectories (creating hierarchical variable names)
- Extracts description from comment lines (starting with #)
- Extracts values from non-comment lines
- Handles different file encodings with fallbacks

### Variable Format
Variables use the `__variable_name__` format, with double underscores on both sides.

#### Variable File Structure
```
# This is a description of the variable
# It can span multiple lines with # prefixes
First value
Second value
Third value
```

### Variable Sources
- Predefined variables loaded from text files
- Collection variables that randomly select from multiple values
- Hierarchical variables organized in subdirectories
- Variables can have descriptions (as comments)

### Variable Processing
The variable substitution is implemented in `prompt_substitution.py`:
```python
def substitute_prompt_vars(prompt: str) -> str:
    # Load all prompt variables
    prompt_vars = load_prompt_vars()
    
    # Pattern to find __variable__ in the prompt
    pattern = r'(__[a-zA-Z0-9_\-/]+__)'
    
    # Iterate until all variables are substituted or max iterations reached
    while iteration < max_iterations:
        matches = re.findall(pattern, substituted_prompt)
        # Process each variable match
```

The variable substitution process:
1. The prompt is scanned for variable patterns using regex
2. For each variable, the system looks up its value from the loaded files
3. If a specific index is provided (`__variable:123__`), it uses that value
4. Otherwise, it selects a random value from the variable list
5. The variable reference is replaced with its actual value
6. If a variable is not found, it remains unchanged in the prompt
7. The process repeats to handle nested variables (variables within variables)

### Variable Naming and Organization
- Variables can be organized in subdirectories for better management
- Variable names from subdirectories include the path: `__subfolder/variable__`
- Variable files can have descriptions using comment lines
- Variables can be listed and explored using the `/list-vars` command

## Command System

### Command Format
Commands use the `/command_name [arguments]` format, with a leading slash.

### Command Types
- Information commands (e.g., `/help`, `/list-vars`, `/history`)
- Action commands (e.g., `/set_var`, `/clear`)
- Workflow modification commands (e.g., `/steps`, `/cfg`)
- System commands (e.g., `/exit`, `/gallery`)
- AI integration commands (for working with AI models)

### Command Processing
1. Commands are identified by the leading slash in the prompt
2. When a command is found, it's extracted and processed
3. Depending on the command type:
   - The command may be removed from the prompt
   - The command may modify the prompt
   - The command may modify workflow properties
   - The command may trigger system actions
   - The command may navigate back to prompt input (using `should_reset_regenerate`)

### Command Result Flags
- `is_command`: Indicates if input was processed as a command
- `should_continue`: Controls whether the main loop should continue
- `should_generate`: Controls whether image generation should proceed
- `should_reset_regenerate`: Controls whether to reset regenerate mode and return to prompt input
- `data`: Optional data returned by the command

### Command Registry
- Commands are loaded from the `commands` directory
- Each command is a Python module that extends `BaseCommand`
- Commands can be added, removed, or modified without changing the core code
- The system automatically discovers and registers commands

### History Command
The `/history` command provides a way to access and reuse previous prompts:
- Displays a table of previously used prompts and commands
- Can filter by type: base-prompt, eval-prompt, or command
- Allows selection and re-use of past prompts
- Returns directly to the prompt input with the selected history item

## Prompt Evaluation Process
1. The user enters a base prompt
2. The system checks for commands and processes them using `evaluate_prompt()`
3. If AI integration is enabled and the prompt contains a ">" character, AI processing is performed
4. The resulting text is scanned for variables
5. Variables are substituted with their values using `substitute_prompt_vars()`
6. The fully evaluated prompt is displayed and used for generation

## Prompt History and State
- The user's base prompt is preserved between sessions
- The system tracks both base and evaluated prompts
- Users can choose to continue with either base or evaluated prompts
- The prompt state is managed by the UserMessages class

## Autocomplete Integration
- The prompt system integrates with tab completion via the `PromptCompleter` class
- Variables and commands are included in completion suggestions
- Completion works anywhere in the prompt, not just at the beginning
- The system detects command patterns starting with `/` and variable patterns with `__`

## AI Integration
- The system can use AI models to enhance prompts
- AI processing is triggered when a prompt contains the ">" character
- Supported AI providers include Ollama, OpenAI, Anthropic, Groq, and Gemini
- The function `evaluate_agents()` handles AI processing of prompts

## Security Considerations
- Command execution is limited to predefined functions
- Variable substitution is sanitized to prevent injection
- User inputs are validated before processing 