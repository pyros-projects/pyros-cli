# Architecture

## Overview
Pyros CLI follows a modular architecture with clear separation of concerns. This document outlines the high-level architecture, code organization, and component interactions.

## Directory Structure

```
pyros_cli/
├── __init__.py          # Package initialization
├── main.py              # Entry point and CLI interaction
├── globals.py           # Global constants and configuration 
├── models/              # Data structures and models
│   ├── __init__.py
│   ├── user_messages.py # User prompt history and state
│   ├── comfyui_workflow.py # ComfyUI workflow representation
│   └── prompt_vars.py   # Variable management
├── services/            # Business logic services
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── gallery.py       # Image gallery functionality
│   ├── preview.py       # Image preview handling
│   ├── prompt_evaluate.py # Prompt evaluation logic
│   ├── prompt_substitution.py # Variable substitution
│   └── commands/        # Command implementations
│       ├── __init__.py
│       ├── base_command.py  # Base command class
│       ├── help_command.py  # Help command implementation
│       ├── list_vars_command.py # List variables command
│       ├── cntrl_command.py # Workflow control command
│       ├── gallery_command.py # Gallery command
│       ├── configure_ai_command.py # AI configuration command
│       └── ...
├── utils/               # Utility functions
│   ├── __init__.py
│   ├── comfy_utils.py   # ComfyUI API utilities
│   └── cli_helper.py    # CLI formatting helpers
├── agents/              # AI agent implementations
│   └── ...
└── library/             # Additional resources
    └── prompt_vars/     # Prompt variable definitions
```

## Data Models

### UserMessages
The `UserMessages` class manages prompt state and history:
```python
class WorkflowProperty(BaseModel):
    node_id: str
    node_property: str
    value: str
    alias: str

class HistoryItem(BaseModel):
    type: Literal["base_prompt", "evaluated_prompt", "command"]
    message: str
    timestamp: str

class UserMessages(BaseModel):
    base_prompt: str    
    evaluated_prompt: str
    command: str
    history: list[HistoryItem]
    session_history: list[HistoryItem]
    workflow_properties: list[WorkflowProperty]
```

Key features:
- Tracks both base and evaluated prompts
- Maintains a history of all messages with timestamps
- Stores workflow property modifications
- Persists across sessions using JSON serialization
- Methods for adding/retrieving messages and properties

### PromptVars
The `PromptVars` class represents prompt variables:
```python
class PromptVars(BaseModel):
    file_path: Optional[str] = None
    prompt_id: Optional[str] = None
    description: Optional[str] = None
    values: list[str] = []
```

### ComfyUISettings
The `ComfyUISettings` class manages configuration:
```python
class ComfyUISettings(BaseModel):
    host: str = "127.0.0.1"
    port: str = "8188"
    file_path: str | None = None
    prompt_node_id: str | None = None
    prompt_node_property: str = "text"
    steps_node_id: str | None = None
    steps_node_property: str = "steps"
    denoise_node_id: str | None = None
    denoise_node_property: str = "seed"
    ai_provider: str | None = None
    model_name: str | None = None
```

## Component Interactions

### Main Flow
1. `main.py` initializes the application and handles the main CLI loop
2. Configuration is loaded from `services/config.py`
3. User prompts are processed through `services/prompt_evaluate.py`
4. Workflow is updated using `utils/comfy_utils.py`
5. API communication is handled through `utils/comfy_utils.py`
6. Image results are saved and optionally displayed

### Command Processing Flow
1. User enters a prompt which may contain commands
2. `CommandRegistry` loads available commands from the commands directory
3. `evaluate_prompt()` checks if input contains commands
4. Commands are extracted and executed by their respective handlers
5. Commands return `CommandResult` objects indicating what to do next
6. The main loop continues based on the command result

### Prompt Evaluation Flow
1. `evaluate_prompt()` processes commands and calls the AI agent if needed
2. `substitute_prompt_vars()` replaces variables with their values
3. The evaluated prompt is stored in the `UserMessages` instance
4. The prompt is included in the workflow sent to ComfyUI

## Core Components

### Models
- **UserMessages**: Maintains prompt history and state
- **ComfyUIWorkflow**: Represents a ComfyUI workflow structure
- **PromptVars**: Manages variables for substitution
- **WorkflowProperty**: Represents a modification to a workflow node

### Services
- **Config**: Handles loading, saving, and verifying configuration
- **Gallery**: Provides image browsing functionality
- **Preview**: Manages image display in terminal or OS viewer
- **PromptEvaluate**: Processes commands and controls prompt evaluation
- **PromptSubstitution**: Handles variable substitution
- **Commands**: Individual command implementations that extend BaseCommand

### Utilities
- **ComfyUtils**: Functions for ComfyUI API interaction and workflow handling
- **CLIHelper**: Utilities for banner display and CLI formatting

### AI Integration
- **Agents**: Implementations for AI-powered prompt enhancement
- **AI Provider Support**: Ollama, OpenAI, Anthropic, Groq, and Gemini

## Design Patterns

### Command Pattern
- Commands are implemented as classes extending BaseCommand
- Each command handles its own functionality
- Commands are registered and dynamically loaded

### Repository Pattern
- Configuration and prompt state are persisted to disk
- Access is abstracted through model methods

### Dependency Injection
- Components receive required dependencies
- Facilitates testing and modularity

### Builder Pattern
- Workflow modifications build up progressively
- Properties can be added/changed incrementally

## Asynchronous Design
- Main CLI loop runs as an async function
- API communication uses async HTTP and WebSocket clients
- Command execution is async to support network operations
- Progress updates and event handling use async patterns

## Error Handling
- Structured error handling with specific exception types
- Clear error messages for user feedback
- Graceful degradation when services are unavailable
- Detailed logging with configurable verbosity levels

## Extension Points
- **Commands**: New commands can be added without modifying core code
- **Variables**: New variable files can be added to the library
- **AI Providers**: Multiple AI provider integrations
- **UI**: Display and formatting can be customized

## Configuration Management
- Settings are loaded at startup
- Connection is verified before operation
- Interactive prompts for missing configuration

## Security Considerations
- Input validation for user commands
- Safe file path handling
- No execution of arbitrary code
- API key management for AI providers 