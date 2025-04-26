# Critical Fixes Implementation Plan

This document provides specific technical guidance for implementing the critical fixes identified in the recommendations.

## 1. Error Handling and Recovery

### WebSocket Connection Resilience

**File**: `src/pyros_cli/utils/comfy_utils.py`  
**Function**: `listen_for_results()`

```python
async def listen_for_results(settings: ComfyUISettings, prompt_id: str, client_id: str):
    # Add connection retry logic
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            ws_url = f"{settings.ws_url}?clientId={client_id}"
            logger.info(f"Connecting to WebSocket (attempt {attempt+1}/{max_retries}): {ws_url}")
            
            async with websockets.connect(ws_url, ping_interval=10, ping_timeout=30) as ws:
                # Existing connection handling
                # ...
                
            # If we get here, connection closed normally
            break
            
        except websockets.exceptions.ConnectionClosed as e:
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                logger.warning(f"WebSocket connection closed ({e}). Retrying in {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to maintain WebSocket connection after {max_retries} attempts.")
                raise ConnectionError(f"Could not maintain connection to ComfyUI: {e}")
```

### Structured Error Types

**New File**: `src/pyros_cli/utils/exceptions.py`

```python
"""
Custom exception types for Pyros CLI.
"""

class PyrosError(Exception):
    """Base exception for all Pyros CLI errors."""
    pass

class ConfigurationError(PyrosError):
    """Raised when there is an issue with configuration."""
    pass

class ConnectionError(PyrosError):
    """Raised when there is an issue connecting to ComfyUI."""
    pass

class WorkflowError(PyrosError):
    """Raised when there is an issue with the workflow."""
    pass

class PromptError(PyrosError):
    """Raised when there is an issue with prompt processing."""
    pass

class APIError(PyrosError):
    """Raised when there is an issue with API responses."""
    pass

class ImageError(PyrosError):
    """Raised when there is an issue with image processing."""
    pass
```

### Error Handler Function

**New File**: `src/pyros_cli/utils/error_handler.py`

```python
"""
Error handling utilities for Pyros CLI.
"""
from rich.console import Console
from loguru import logger
from pyros_cli.utils.exceptions import *

console = Console()

def handle_error(error: Exception, exit_on_critical=False):
    """
    Handle exceptions in a consistent way across the application.
    
    Args:
        error: The exception to handle
        exit_on_critical: Whether to exit the application on critical errors
    
    Returns:
        bool: True if the error was handled, False if it should be re-raised
    """
    if isinstance(error, ConfigurationError):
        console.print(f"[bold red]Configuration Error:[/] {str(error)}")
        console.print("Please run the application with the --reconfigure flag to fix this issue.")
        if exit_on_critical:
            return False
            
    elif isinstance(error, ConnectionError):
        console.print(f"[bold red]Connection Error:[/] {str(error)}")
        console.print("Please check that ComfyUI is running and accessible.")
        console.print("Try the following:")
        console.print("  1. Ensure ComfyUI server is running")
        console.print("  2. Check the host and port configuration")
        console.print("  3. Verify network connectivity")
        if exit_on_critical:
            return False
            
    elif isinstance(error, WorkflowError):
        console.print(f"[bold red]Workflow Error:[/] {str(error)}")
        console.print("There was an issue with your workflow file or its configuration.")
        console.print("Please check that your workflow is valid and all required nodes exist.")
        
    elif isinstance(error, PromptError):
        console.print(f"[bold yellow]Prompt Processing Error:[/] {str(error)}")
        console.print("Your prompt could not be processed. Please check your syntax.")
        
    elif isinstance(error, APIError):
        console.print(f"[bold red]API Error:[/] {str(error)}")
        console.print("There was an error communicating with ComfyUI.")
        
    elif isinstance(error, ImageError):
        console.print(f"[bold yellow]Image Error:[/] {str(error)}")
        console.print("There was an error processing or saving an image.")
        
    else:
        console.print(f"[bold red]Unexpected Error:[/] {str(error)}")
        logger.exception("Unexpected error details:")
        if exit_on_critical:
            return False
    
    return True
```

## 2. Security Improvements for API Keys

### Secure Credential Storage

**New File**: `src/pyros_cli/services/credentials.py`

```python
"""
Secure credential management for API keys.
"""
import os
import keyring
import platform
from getpass import getpass
from typing import Optional
from loguru import logger

SERVICE_NAME = "pyros-cli"

def get_credential(key_name: str) -> Optional[str]:
    """
    Get a credential from the secure store or environment variable.
    
    Args:
        key_name: The name of the credential (e.g. 'OPENAI_API_KEY')
        
    Returns:
        str or None: The credential value or None if not found
    """
    # First check environment variable
    if key_name in os.environ:
        return os.environ[key_name]
    
    # Then check keyring
    try:
        credential = keyring.get_password(SERVICE_NAME, key_name)
        if credential:
            return credential
    except Exception as e:
        logger.warning(f"Could not access secure credential store: {e}")
    
    return None

def set_credential(key_name: str, value: str) -> bool:
    """
    Set a credential in the secure store.
    
    Args:
        key_name: The name of the credential
        value: The value to store
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.set_password(SERVICE_NAME, key_name, value)
        return True
    except Exception as e:
        logger.error(f"Could not store credential securely: {e}")
        return False

def prompt_for_credential(key_name: str, description: str) -> Optional[str]:
    """
    Prompt the user for a credential value.
    
    Args:
        key_name: The name of the credential
        description: A description of what the credential is for
        
    Returns:
        str or None: The credential value or None if canceled
    """
    print(f"\n{description}")
    print(f"Please enter your {key_name}:")
    value = getpass()
    
    if not value.strip():
        return None
        
    if set_credential(key_name, value):
        print(f"{key_name} saved securely.")
        return value
    else:
        print(f"Could not save {key_name} securely. Using for this session only.")
        return value

def clear_credential(key_name: str) -> bool:
    """
    Remove a credential from the secure store.
    
    Args:
        key_name: The name of the credential
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        keyring.delete_password(SERVICE_NAME, key_name)
        return True
    except Exception as e:
        logger.error(f"Could not delete credential: {e}")
        return False
```

### Updated AI Configuration Command

**File**: `src/pyros_cli/services/commands/configure_ai_command.py`

```python
# Update execute method to use secure credentials
async def execute(self, args: str) -> CommandResult:
    """Configure AI with format: /configure-ai <ollama|openai|anthropic|groq|gemini>"""
    
    # ...existing implementation...
    
    # For OpenAI example:
    if ai_provider == "openai":
        model_name = await questionary.text("Enter the openai model name (eg: gpt-4o): ").ask_async()
        model_name = "openai/" + model_name.strip()
        set_key(dotenv_path, "MODEL_NAME", model_name)
        os.environ["MODEL_NAME"] = model_name

        # Instead of storing in .env, use secure credential storage
        api_key = get_credential("OPENAI_API_KEY")
        if not api_key:
            api_key = await prompt_for_credential(
                "OPENAI_API_KEY",
                "An OpenAI API key is required."
            )
            if not api_key:
                print_error("API key is required. Configuration canceled.")
                return CommandResult(is_command=True, should_generate=False, data=False)
        
        os.environ["OPENAI_API_KEY"] = api_key
        print_success(f"AI provider set to {ai_provider} with model {model_name}")
        
    # ...similar changes for other providers...
```

## 3. Input Validation

### Pydantic Model Validators

**File**: `src/pyros_cli/models/user_messages.py`

```python
from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
import re
import os

class WorkflowProperty(BaseModel):
    node_id: str
    node_property: str
    value: str
    alias: str
    
    @validator('node_id')
    def validate_node_id(cls, v):
        if not v or not v.strip():
            raise ValueError("Node ID cannot be empty")
        return v.strip()
    
    @validator('node_property')
    def validate_node_property(cls, v):
        if not v or not v.strip():
            raise ValueError("Node property cannot be empty")
        return v.strip()

class HistoryItem(BaseModel):
    type: Literal["base_prompt", "evaluated_prompt", "command"]
    message: str
    timestamp: str
    
    @validator('message')
    def validate_message(cls, v):
        # Maximum reasonable message length
        if len(v) > 10000:
            raise ValueError("Message too long (exceeds 10000 characters)")
        return v

class UserMessages(BaseModel):
    base_prompt: str    
    evaluated_prompt: str
    command: str
    history: List[HistoryItem]
    session_history: List[HistoryItem] = Field(default_factory=list)
    workflow_properties: List[WorkflowProperty]
    
    @validator('base_prompt', 'evaluated_prompt')
    def validate_prompt(cls, v):
        # Sanitize control characters
        v = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        return v
    
    # ... rest of the implementation ...
```

### Path Validation

**New File**: `src/pyros_cli/utils/path_utils.py`

```python
"""
Utilities for safe path handling.
"""
import os
from pathlib import Path
from typing import Optional

def is_safe_path(base_path: str, path: str) -> bool:
    """
    Check if a path is safe (doesn't escape the base directory).
    
    Args:
        base_path: The base directory path
        path: The path to check
        
    Returns:
        bool: True if the path is safe, False otherwise
    """
    # Convert to absolute paths
    base_abs = os.path.abspath(base_path)
    path_abs = os.path.abspath(os.path.join(base_path, path))
    
    # Check if the path is within the base directory
    return os.path.commonpath([base_abs]) == os.path.commonpath([base_abs, path_abs])

def safe_join_path(base_path: str, *paths) -> Optional[str]:
    """
    Safely join paths ensuring they don't escape the base directory.
    
    Args:
        base_path: The base directory path
        *paths: Path components to join
        
    Returns:
        str or None: The joined path if safe, None otherwise
    """
    joined = os.path.join(base_path, *paths)
    
    if not is_safe_path(base_path, joined):
        return None
        
    return joined
```

### Input Sanitization for Prompts

**File**: `src/pyros_cli/services/prompt_evaluate.py`

```python
# Add to evaluate_prompt function
async def evaluate_prompt(user_input: str) -> CommandResult:
    """
    Evaluate user input to determine if it's a command
    Returns CommandResult with processing information
    """
    # Sanitize input
    if user_input:
        # Remove potentially harmful characters
        user_input = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', user_input)
        
        # Limit input length
        if len(user_input) > 10000:
            console.print("Warning: Input too long, truncating to 10000 characters.", style="yellow")
            user_input = user_input[:10000]
    
    # Rest of the implementation
    registry = CommandRegistry()
    # Load any additional commands from directory
    registry.load_commands_from_directory()
    return await registry.evaluate(user_input)
```

## Implementation Strategy

1. Start by implementing the error handling framework (`exceptions.py` and `error_handler.py`)
2. Gradually integrate the error handling into existing code, starting with `comfy_utils.py`
3. Implement the secure credential storage and update the AI configuration command
4. Add input validation to models and key input processing functions
5. Add comprehensive type hints throughout the codebase
6. Test each component thoroughly after implementation

This implementation plan addresses the most critical security and stability issues while providing a framework for further improvements. 