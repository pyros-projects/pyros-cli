# config.py
import asyncio
import os
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv, set_key
import questionary
from rich.console import Console
from pyros_cli.utils.cli_helper import print_error, print_success, print_subheader
import aiohttp # Use aiohttp for async connection check

console = Console()


class ComfyUISettings(BaseModel):
    host: str = "127.0.0.1"
    port: str = "8188"
    file_path: str | None = None
    prompt_node_id: str | None = None
    prompt_node_property: str = "text" # Default often 'text'
    steps_node_id: str | None = None
    steps_node_property: str = "steps" # Default often 'steps'
    denoise_node_id: str | None = None
    denoise_node_property: str = "seed" # Default often 'seed'
    ai_provider: str| None = None
    model_name: str| None = None


    @property
    def http_url(self):
        return f"http://{self.host}:{self.port}"

    @property
    def ws_url(self):
         return f"ws://{self.host}:{self.port}/ws"

def _get_env_path():
    return ".env"

def load_config() -> ComfyUISettings:
    """Loads configuration from .env file, filling missing values with defaults."""
    dotenv_path = _get_env_path()
    load_dotenv(dotenv_path=dotenv_path)

    # Create settings instance with defaults, overridden by .env values
    settings_data = {
        "host": os.getenv("COMFYUI_HOST", "127.0.0.1"),
        "port": os.getenv("COMFYUI_PORT", "8188"),
        "file_path": os.getenv("COMFYUI_FILE_PATH"),
        "prompt_node_id": os.getenv("COMFYUI_PROMPT_NODE_ID"),
        "prompt_node_property": os.getenv("COMFYUI_PROMPT_NODE_PROPERTY", "text"),
        "steps_node_id": os.getenv("COMFYUI_STEPS_NODE_ID"),
        "steps_node_property": os.getenv("COMFYUI_STEPS_NODE_PROPERTY", "steps"),
        "denoise_node_id": os.getenv("COMFYUI_DENOISE_NODE_ID"),
        "denoise_node_property": os.getenv("COMFYUI_DENOISE_NODE_PROPERTY", "seed"),
        "ai_provider": os.getenv("AI_PROVIDER"),
        "model_name": os.getenv("MODEL_NAME"),
    }
    try:
        return ComfyUISettings(**settings_data)
    except ValidationError as e:
        print_error(f"Configuration validation error: {e}")
        # Return default settings on validation error
        return ComfyUISettings()


def save_config(settings: ComfyUISettings):
    """Saves the current configuration to the .env file."""
    dotenv_path = _get_env_path()
    set_key(dotenv_path, "COMFYUI_HOST", settings.host)
    set_key(dotenv_path, "COMFYUI_PORT", settings.port)
    if settings.file_path:
        set_key(dotenv_path, "COMFYUI_FILE_PATH", settings.file_path)
    if settings.prompt_node_id:
        set_key(dotenv_path, "COMFYUI_PROMPT_NODE_ID", settings.prompt_node_id)
    set_key(dotenv_path, "COMFYUI_PROMPT_NODE_PROPERTY", settings.prompt_node_property)
    if settings.steps_node_id:
        set_key(dotenv_path, "COMFYUI_STEPS_NODE_ID", settings.steps_node_id)
    set_key(dotenv_path, "COMFYUI_STEPS_NODE_PROPERTY", settings.steps_node_property)
    if settings.denoise_node_id:
        set_key(dotenv_path, "COMFYUI_DENOISE_NODE_ID", settings.denoise_node_id)
    set_key(dotenv_path, "COMFYUI_DENOISE_NODE_PROPERTY", settings.denoise_node_property)
    print_success("Configuration saved to .env file.")


async def check_connection(settings: ComfyUISettings) -> bool:
    """Checks the connection to ComfyUI asynchronously."""
    url = settings.http_url
    print_subheader(f"Checking connection to {url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    print_success("Connection successful!")
                    return True
                else:
                    print_error(f"Connection failed! Status code: {response.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print_error("Connection failed! Host unreachable or wrong port.")
        return False
    except asyncio.TimeoutError:
        print_error("Connection failed! Request timed out.")
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred during connection check: {e}")
        return False

async def prompt_for_config(current_settings: ComfyUISettings) -> ComfyUISettings:
    """Interactively prompts the user for configuration settings."""
    settings = current_settings.copy() # Work on a copy

    # --- Host and Port ---
    while True:
        console.line()
        host = await questionary.text(
            "Enter ComfyUI IP address:", default=settings.host
        ).ask_async()
        port = await questionary.text(
            "Enter ComfyUI port:", default=settings.port
        ).ask_async()

        if not host or not port:
            print_error("Host and Port cannot be empty.")
            continue

        temp_settings = settings.copy(update={'host': host, 'port': port})
        if await check_connection(temp_settings):
            settings.host = host
            settings.port = port
            break
        else:
            print_error("Connection failed with entered details. Please try again.")

    # --- Workflow File ---
    console.line()
    if not settings.file_path or not os.path.exists(settings.file_path):
        if settings.file_path:
             print_error(f"Saved workflow file not found: {settings.file_path}")
        while True:
            file_path = await questionary.path(
                "Select your ComfyUI API export *.json file:"
            ).ask_async()
            if file_path and os.path.exists(file_path) and file_path.endswith(".json"):
                 settings.file_path = file_path
                 break
            elif file_path:
                 print_error("Invalid selection. Please select a valid .json file.")
            else:
                 print_error("File selection is required.")
                 # You might want to exit here if a file is mandatory
    else:
        console.print(f"Using workflow file: {settings.file_path}")


    # --- Node IDs and Properties ---
    console.line()
    print_subheader("Workflow Node Configuration")
    console.print("Enter the Node ID and Property Name for specific inputs.")

    settings.prompt_node_id = await questionary.text(
        "Prompt Text Node ID:", default=settings.prompt_node_id or ""
    ).ask_async()
    settings.prompt_node_property = await questionary.text(
        "Prompt Text Property Name:", default=settings.prompt_node_property or "text"
    ).ask_async()

    settings.steps_node_id = await questionary.text(
        "Steps Node ID:", default=settings.steps_node_id or ""
    ).ask_async()
    settings.steps_node_property = await questionary.text(
        "Steps Property Name:", default=settings.steps_node_property or "steps"
    ).ask_async()

    settings.denoise_node_id = await questionary.text(
        "Seed/Noise Node ID:", default=settings.denoise_node_id or ""
    ).ask_async()
    settings.denoise_node_property = await questionary.text(
        "Seed/Noise Property Name:", default=settings.denoise_node_property or "seed"
    ).ask_async()

    # Validate required fields
    if not all([settings.file_path, settings.prompt_node_id, settings.steps_node_id, settings.denoise_node_id]):
         print_error("File path, prompt node ID, steps node ID, and seed node ID are required.")
         # Consider exiting or re-prompting if essential info is missing
         # For now, we return the possibly incomplete settings
         # raise ValueError("Essential configuration missing.") # Or handle more gracefully

    return settings