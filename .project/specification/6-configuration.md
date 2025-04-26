# Configuration Management

## Overview
Pyros CLI uses a robust configuration system to manage connection settings, workflow details, and user preferences. The configuration is persistent across sessions and includes interactive setup for first-time users.

## Configuration File Structure
The configuration is stored as environment variables in a `.env` file with the following main settings:

```
COMFYUI_HOST=localhost
COMFYUI_PORT=8188
COMFYUI_FILE_PATH=/path/to/workflow.json
COMFYUI_PROMPT_NODE_ID=12345
COMFYUI_PROMPT_NODE_PROPERTY=text
COMFYUI_STEPS_NODE_ID=67890
COMFYUI_STEPS_NODE_PROPERTY=steps
COMFYUI_DENOISE_NODE_ID=abcde
COMFYUI_DENOISE_NODE_PROPERTY=seed
AI_PROVIDER=
MODEL_NAME=
```

## Configuration Implementation
Configuration is implemented using:
- The `dotenv` package for reading/writing environment variables
- `pydantic` for validation and type checking with the `ComfyUISettings` class

## Configuration Management Functions

### Loading Configuration
- `load_config()` reads from the `.env` file in the current directory
- Creates default configuration if file doesn't exist
- Validates loaded configuration using pydantic
- Returns a `ComfyUISettings` object used throughout the application

### Saving Configuration
- `save_config()` serializes the settings object to environment variables
- Writes to the `.env` file using the `set_key` function from dotenv
- Creates parent directories if they don't exist
- Handles permissions and file errors

### Prompting for Configuration
- `prompt_for_config()` provides an interactive questionnaire for configuration
- Uses `questionary` for user-friendly prompts
- Provides sensible defaults and validation
- Connection testing to verify settings before saving

## Connection Verification
- `check_connection()` tests connection to ComfyUI server using the current settings
- Uses aiohttp to send a simple HTTP request
- Reports connection status with user-friendly messages
- Times out after 5 seconds if the server doesn't respond

## Configuration Properties
The `ComfyUISettings` class provides:
- Basic validation of configuration values
- Default values for common settings
- Helper properties like `http_url` and `ws_url` to construct API endpoints

## Configuration Update Process
1. The application loads existing configuration on startup
2. Connection to ComfyUI is tested with `check_connection()`
3. If connection fails or user requests reconfiguration:
   - The interactive prompt sequence begins with `prompt_for_config()`
   - User enters new values or accepts defaults
   - New configuration is tested
   - If successful, configuration is saved with `save_config()`
4. Required settings are verified before proceeding

## Required Configuration Fields

| Field | Description | Default | Environment Variable |
|-------|-------------|---------|---------------------|
| `host` | ComfyUI server hostname | `127.0.0.1` | `COMFYUI_HOST` |
| `port` | ComfyUI server port | `8188` | `COMFYUI_PORT` |
| `file_path` | Path to workflow JSON file | None | `COMFYUI_FILE_PATH` |
| `prompt_node_id` | ID of the text prompt node | None | `COMFYUI_PROMPT_NODE_ID` |
| `prompt_node_property` | Property name for the prompt | `text` | `COMFYUI_PROMPT_NODE_PROPERTY` |
| `steps_node_id` | ID of the sampling steps node | None | `COMFYUI_STEPS_NODE_ID` |
| `steps_node_property` | Property name for the steps | `steps` | `COMFYUI_STEPS_NODE_PROPERTY` |
| `denoise_node_id` | ID of the seed node | None | `COMFYUI_DENOISE_NODE_ID` |
| `denoise_node_property` | Property name for the seed | `seed` | `COMFYUI_DENOISE_NODE_PROPERTY` |
| `ai_provider` | Optional AI provider for prompt enhancement | None | `AI_PROVIDER` |
| `model_name` | Optional AI model name | None | `MODEL_NAME` |

## Optional Advanced Configuration
- AI integration settings for prompt enhancement
- Custom workflow properties defined through commands

## Error Handling
- Validation errors are caught and reported with clear messages
- Network errors during connection testing are handled gracefully
- Fallback to default values when configuration is invalid

## Configuration Location
The configuration file is stored in a platform-specific location:

- Windows: `%APPDATA%\pyros-cli\config.json`
- macOS: `~/Library/Application Support/pyros-cli/config.json`
- Linux: `~/.config/pyros-cli/config.json`

## Configuration Security
- Configuration file permissions are set to user-only read/write
- No sensitive data (like API keys) is currently stored
- File paths are validated before use to prevent directory traversal 