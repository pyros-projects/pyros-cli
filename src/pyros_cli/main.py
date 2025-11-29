# main.py
import asyncio
import random
import os
import sys
import aiohttp
import questionary
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, SpinnerColumn, TimeElapsedColumn
from loguru import logger
import websockets
from prompt_toolkit.completion import Completer, Completion

# Local imports
from pyros_cli.models.user_messages import UserMessages, WorkflowProperty
from pyros_cli.services.config import (
    load_config, save_config,
    check_connection, prompt_for_config
)
from pyros_cli.services.gallery import show_gallery
from pyros_cli.utils.comfy_utils import (
    load_workflow, update_workflow, send_prompt,
    listen_for_results, fetch_and_save_final_images
)
from pyros_cli.services.preview import display_final_image_os
from pyros_cli.utils.cli_helper import banner_text # Your banner function
from pyros_cli.utils.cli_helper import print_header, print_error, print_success
from pyros_cli.services.prompt_evaluate import evaluate_prompt, CommandRegistry
from pyros_cli.models.prompt_vars import load_prompt_vars


file_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))

console = Console()



# Configure Loguru
def setup_logging():
    logger.remove()
    log_level = os.getenv("LOG_LEVEL", "CRITICAL").upper()
    valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    if log_level not in valid_levels:
        print(f"Invalid LOG_LEVEL: {log_level}. Defaulting to INFO.")
        log_level = "CRITICAL"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<level>{level: <8}</level> | <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    logger.info(f"Logger configured with level: {log_level}")

# Custom completer that works anywhere in the prompt, not just at the beginning
class PromptCompleter(Completer):
    def __init__(self, choices):
        self.choices = choices
        # Extract commands without the leading slash for better matching
        self.commands = [cmd[1:] if cmd.startswith('/') else cmd for cmd in choices if cmd.startswith('/')]
        # Keep prompt variables as they are
        self.vars = [var for var in choices if not var.startswith('/')]
    
    def get_completions(self, document, complete_event):
        # Get text before cursor and current word
        text_before_cursor = document.text_before_cursor
        
        # Get the current position 
        cursor_position = len(text_before_cursor)
        
        # Find commands - they must start with /
        if '/' in text_before_cursor:
            last_slash_pos = text_before_cursor.rfind('/')
            # If we're typing right after a slash, suggest commands
            if cursor_position > last_slash_pos:
                current_word = text_before_cursor[last_slash_pos+1:].strip()
                for command in self.commands:
                    if command.startswith(current_word):
                        # Only complete the command part, not the entire input
                        completion_text = command
                        yield Completion(
                            completion_text, 
                            start_position=-len(current_word),
                            display=f"{command}"
                        )
        
        # Find prompt variables - looking for partial "__var" matches
        if '__' in text_before_cursor:
            # Find the last occurrence of "__" to get the start of a potential variable
            last_var_start = text_before_cursor.rfind('__')
            # Check if we're typing after a "__" and it doesn't already have a closing "__"
            if cursor_position > last_var_start and text_before_cursor.count('__', last_var_start) == 1:
                # Get the current partial variable name
                current_var = text_before_cursor[last_var_start:]
                
                # Check if we're in the process of typing an index
                if ':' in current_var:
                    # We're typing an index, don't provide completions
                    # We could possibly provide index suggestions here in the future
                    pass
                else:
                    for var in self.vars:
                        # If the variable starts with what we've typed so far
                        if var.startswith(current_var):
                            # Only complete the rest of the variable
                            completion_text = var[len(current_var):]
                            yield Completion(
                                completion_text, 
                                start_position=0,
                                display=var
                            )

# Function to get autocomplete suggestions for prompt variables and commands
def get_autocomplete_suggestions():
    # Load all available prompt variables
    prompt_vars = load_prompt_vars()
    
    # Load all commands
    command_registry = CommandRegistry()
    command_registry.load_commands_from_directory()
    
    # Get command suggestions (with leading /)
    command_suggestions = [cmd for cmd in command_registry.commands.keys()]
    
    # Get prompt variable suggestions
    var_suggestions = list(prompt_vars.keys())
    
    # Combine all suggestions
    all_suggestions = command_suggestions + var_suggestions
    
    return all_suggestions

async def start_cli():
    banner_text()
    setup_logging()
    print_header("ComfyUI Settings")

    user_messages = UserMessages.load_from_file()

    # --- Configuration ---
    settings = load_config()
    console.print("Current configuration:", style="yellow")
    console.print(f" Host: {settings.host}:{settings.port}")
    # Add other settings if needed

    console.print(f" Workflow: {settings.file_path or 'Not set'}")
    console.print(f" Prompt node ID: {settings.prompt_node_id or 'Not set'}")
    console.print(f" Prompt node property: {settings.prompt_node_property or 'Not set'}")
    console.print(f" Steps node ID: {settings.steps_node_id or 'Not set'}")
    console.print(f" Steps node property: {settings.steps_node_property or 'Not set'}")
    console.print(f" Noise node ID: {settings.denoise_node_id or 'Not set'}")
    console.print(f" Noise node property: {settings.denoise_node_property or 'Not set'}")

    console.line()

    if not await check_connection(settings):
        print_error("Initial connection failed. Please verify settings.")
        settings = await prompt_for_config(settings) # Re-prompt if initial check fails
        save_config(settings) # Save the potentially updated config
    else:
        console.line()
        # Optionally ask if user wants to reconfigure even if connection works
        reconfigure = await questionary.confirm("Connection successful. Reconfigure settings?", default=False).ask_async()
        if reconfigure:
            settings = await prompt_for_config(settings)
            save_config(settings)

    
    # Ensure essential settings are present after prompting
    if not all([settings.file_path, settings.prompt_node_id, settings.steps_node_id, settings.denoise_node_id]):
        print_error("Essential configuration (workflow file, node IDs) is missing. Exiting.")
        return
    
    

    # --- Load Workflow ---
    try:
        base_workflow = load_workflow(settings.file_path)
    except Exception:
        print_error(f"Failed to load workflow file: {settings.file_path}. Please check the file and configuration.")
        return # Exit if workflow cannot be loaded

    # --- Main Loop ---
    print_header("Prompt Playground")
    console.print("Enter your prompt below. Type 'exit' or 'quit' to stop. Use /help for commands.")
    console.line()

    last_prompt = ""
    regenerate_mode = False
    keep_seed = False
    number_of_images = 1
    final_image_paths = []

    # Get the autocomplete suggestions once before the loop
    autocomplete_choices = get_autocomplete_suggestions()
    
    # Create our custom completer
    custom_completer = PromptCompleter(autocomplete_choices)

    while True:
        # if not regenerate_mode:
            # Ask for new prompt

        if not regenerate_mode:
            current_prompt = await questionary.text(
                "",
                default=user_messages.get_base_prompt(),
                completer=custom_completer
            ).ask_async()

            user_messages.set_base_prompt(current_prompt)

            

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[cyan]Generating {number_of_images} image(s)...", total=number_of_images)
            # Either ask for new prompt or use last prompt
            for i in range(number_of_images):
                
                current_prompt = user_messages.get_base_prompt()
                if current_prompt is None or current_prompt.lower() in ["exit", "quit"]:
                    console.print("Exiting playground.", style="bold yellow")
                    break
                
                # Process commands
                command_result = await evaluate_prompt(current_prompt)
                if command_result.is_command:
                    if not command_result.should_continue:
                        break
                        
                    if not command_result.should_generate:
                        continue
                        
                    # Check if the command returned a WorkflowProperty
                    if isinstance(command_result.data, WorkflowProperty):
                        # Add the workflow property to the user messages
                        user_messages.add_workflow_property(command_result.data)
                        console.print(f"[bold green]Workflow property added:[/] Node: {command_result.data.node_id}, Property: {command_result.data.node_property}, Value: {command_result.data.value}")
                        
                    # If we get here, the command was processed but we should still generate
                    # This would be for commands that modify the prompt and still want generation
                    elif command_result.data:
                        current_prompt = command_result.data
                elif command_result.data:
                    # If not command data contains the evaluated prompt
                    current_prompt = command_result.data
                        
                # Skip generation if command was processed and indicated not to generate
                if not regenerate_mode and command_result.is_command and not command_result.should_generate:
                    continue

                user_messages.set_evaluated_prompt(current_prompt)

                # --- Generate ---
                if not keep_seed:
                    seed = random.randint(0, 2**32 - 1) # Use full 32-bit range for seed
                logger.info(f"Using Seed: {seed}")
                logger.info(f"Using Prompt: '{current_prompt}'")

                try:
                    progress.update(task, description=f"[cyan]Generating image {i+1}/{number_of_images}: Processing...")
                    # Update workflow dict for this run
                    updated_workflow_dict = update_workflow(base_workflow, current_prompt, seed, settings, user_messages)

                    # Send prompt to ComfyUI
                    prompt_id, client_id = await send_prompt(settings, updated_workflow_dict)

                    # Listen for results (includes previews)
                    await listen_for_results(settings, prompt_id, client_id)

                    # Fetch and save final image(s)
                    final_image_paths = await fetch_and_save_final_images(settings, prompt_id, current_prompt)

                   

                    #print_success("Image generation process complete!")
                    progress.update(task, advance=1, description=f"[green]Image {i+1}/{number_of_images} completed")

                except (aiohttp.ClientError, websockets.exceptions.WebSocketException, ConnectionRefusedError) as e:
                    print_error(f"Communication error with ComfyUI: {e}")
                    print_error("Please ensure ComfyUI is running and accessible.")
                    # Decide if you want to retry or exit here
                    break # Exit on communication error
                except FileNotFoundError:
                    print_error(f"Workflow file error. Ensure '{settings.file_path}' exists.")
                    break
                except Exception as e:
                    print_error(f"An unexpected error occurred during generation: {e}")
                    logger.exception("Detailed error:") # Log full traceback
                    # Continue to next prompt or break? Let's continue for now.

            #progress.update(task, advance=1, description=f"[red]Image {i+1}/{number_of_images} done")
            progress.stop()

         # Display final image using OS viewer (optional)
        if final_image_paths and number_of_images == 1:
            # Attempt to show the first final image
            show_image  = await questionary.confirm("Show Image?", default=False).ask_async()
            if show_image:
                display_final_image_os(final_image_paths[0])
        else:
            logger.warning("No final images were saved.")


        # --- Ask for next action ---
        console.line()
        next_action = await questionary.select(
            "What next?",
            choices=[
                questionary.Choice("Continue with base prompt", "base"),
                questionary.Choice("Continue with evaluated prompt", "evaluated"),
                questionary.Choice("Regenerate Base Prompt", "regenerate_base"),
                questionary.Choice("Regenerate Evaluated Prompt", "regenerate_evaluated"),
                questionary.Choice("Quit", "quit"),
            ],
            use_shortcuts=True, # Allows typing 'n', 'r', 'q'
        ).ask_async()

        

        if next_action == "base":
            keep_seed = await questionary.confirm("Keep the same seed?", default=False).ask_async()
            number_of_images = 1
            regenerate_mode = False
        elif next_action == "evaluated":
            keep_seed = await questionary.confirm("Keep the same seed?", default=False).ask_async()
            number_of_images = 1
            user_messages.set_base_prompt(current_prompt)
            regenerate_mode = False
        elif next_action == "regenerate_base":
            number_of_images = int(await questionary.text(
                "How many images?",
                default="1",
            ).ask_async())
            keep_seed = False
            regenerate_mode = True
            #user_messages.set_base_prompt(current_prompt)
        elif next_action == "regenerate_evaluated":
            number_of_images = int(await questionary.text(
                "How many images?",
                default="1",
            ).ask_async())
            keep_seed = False
            regenerate_mode = True
            user_messages.set_base_prompt(current_prompt)
        elif next_action == "quit":
            console.print("Exiting playground.", style="bold yellow")
            break
            

        console.line() # Separator for next iteration


if __name__ == "__main__":
    # On Windows, the default event loop policy might cause issues with subprocesses
    # If you encounter problems opening the image viewer on Windows, try uncommenting this:
    # if platform.system() == "Windows":
    #    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(start_cli())
    except KeyboardInterrupt:
        console.print("\nExiting due to user interrupt.", style="bold red")
    except Exception as e:
         # Catch unexpected errors during shutdown or setup
         logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)