# comfy_utils.py
import json
import uuid
import os
from typing import Any, Dict, List, Tuple
from pydantic import ValidationError
import websockets
import aiohttp
from loguru import logger
from pyros_cli.models.comfyui_workflow import ComfyUIWorkflow
from pyros_cli.services.config import ComfyUISettings # Import settings model
from pyros_cli.services.preview import get_preview_renderable # Import preview function
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.text import Text
from rich.live import Live
from pyros_cli.models.user_messages import UserMessages

console = Console() # Make console available for final print


# --- Rich Live Patch for crop_above support ---
# This patch allows Rich's Live widget to crop content from the TOP instead of the bottom,
# keeping the progress bar and status visible while the preview image gets cropped if too tall.
_live_patch_applied = False


def _ensure_live_crop_above() -> None:
    """Monkeypatch rich.live_render to support 'crop_above' overflow.
    
    This keeps the bottom content (progress bar, status) visible while
    cropping the top (preview image) when content exceeds terminal height.
    """
    global _live_patch_applied
    if _live_patch_applied:
        return
    try:
        from typing import Literal as _Literal
        from rich import live_render as _lr
    except Exception:
        return

    # Extend the accepted literal at runtime
    current_args = getattr(_lr.VerticalOverflowMethod, "__args__", ())
    if "crop_above" not in current_args:
        _lr.VerticalOverflowMethod = _Literal[
            "crop", "crop_above", "ellipsis", "visible"
        ]  # type: ignore[assignment]

    if getattr(_lr.LiveRender.__rich_console__, "_pyros_crop_above", False):
        _live_patch_applied = True
        return

    Segment = _lr.Segment
    Text = _lr.Text
    loop_last = _lr.loop_last

    def _patched_rich_console(self, console, options):
        renderable = self.renderable
        style = console.get_style(self.style)
        lines = console.render_lines(renderable, options, style=style, pad=False)
        shape = Segment.get_shape(lines)

        _, height = shape
        max_height = options.size.height
        if height > max_height:
            if self.vertical_overflow == "crop":
                lines = lines[:max_height]
                shape = Segment.get_shape(lines)
            elif self.vertical_overflow == "crop_above":
                lines = lines[-max_height:]
                shape = Segment.get_shape(lines)
            elif self.vertical_overflow == "ellipsis" and max_height > 0:
                lines = lines[: (max_height - 1)]
                overflow_text = Text(
                    "...",
                    overflow="crop",
                    justify="center",
                    end="",
                    style="live.ellipsis",
                )
                lines.append(list(console.render(overflow_text)))
                shape = Segment.get_shape(lines)
        self._shape = shape

        new_line = Segment.line()
        for last, line in loop_last(lines):
            yield from line
            if not last:
                yield new_line

    _patched_rich_console._pyros_crop_above = True  # type: ignore[attr-defined]
    _lr.LiveRender.__rich_console__ = _patched_rich_console
    _live_patch_applied = True


# Apply the patch on module import
_ensure_live_crop_above()


# --- Workflow Handling ---

def load_workflow(filepath: str) -> ComfyUIWorkflow:
    """Loads workflow from a JSON file."""
    logger.info(f"Loading workflow from: {filepath}")
    try:
        with open(filepath, 'r') as f:
            raw_json = json.load(f)
        workflow = ComfyUIWorkflow.model_validate(raw_json)
        logger.success("Workflow loaded successfully.")
        return workflow
    except FileNotFoundError:
        logger.error(f"Workflow file not found: {filepath}")
        raise
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in workflow file: {filepath}")
        raise
    except ValidationError as e:
        logger.error(f"Workflow validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred loading workflow: {e}")
        raise


def update_workflow(
    workflow: ComfyUIWorkflow,
    prompt_text: str,
    seed: int,
    settings: ComfyUISettings,
    user_messages: UserMessages
) -> Dict[str, Any]:
    """Updates the workflow dictionary with new prompt and seed."""
    workflow_dict = workflow.model_dump(mode='python') # Get a mutable dict

    # Update Prompt
    if settings.prompt_node_id and settings.prompt_node_id in workflow_dict:
        if settings.prompt_node_property in workflow_dict[settings.prompt_node_id]['inputs']:
            workflow_dict[settings.prompt_node_id]['inputs'][settings.prompt_node_property] = prompt_text
            logger.debug(f"Updated prompt in node '{settings.prompt_node_id}', property '{settings.prompt_node_property}'.")
        else:
            logger.warning(f"Property '{settings.prompt_node_property}' not found in inputs of node '{settings.prompt_node_id}'. Prompt not updated.")
    else:
        logger.warning(f"Prompt node ID '{settings.prompt_node_id}' not found in workflow. Prompt not updated.")

    # Update Seed
    if settings.denoise_node_id and settings.denoise_node_id in workflow_dict:
        if settings.denoise_node_property in workflow_dict[settings.denoise_node_id]['inputs']:
            workflow_dict[settings.denoise_node_id]['inputs'][settings.denoise_node_property] = seed
            logger.debug(f"Updated seed in node '{settings.denoise_node_id}', property '{settings.denoise_node_property}'.")
        else:
            logger.warning(f"Property '{settings.denoise_node_property}' not found in inputs of node '{settings.denoise_node_id}'. Seed not updated.")
    else:
        logger.warning(f"Seed node ID '{settings.denoise_node_id}' not found in workflow. Seed not updated.")

    # Update Workflow Properties
    if user_messages.workflow_properties:
        for property in user_messages.workflow_properties:
            if property.node_id in workflow_dict:
                workflow_dict[property.node_id]['inputs'][property.node_property] = property.value
                logger.debug(f"Updated workflow property in node '{property.node_id}', property '{property.node_property}'.")
            else:
                logger.warning(f"Node ID '{property.node_id}' not found in workflow. Property not updated.")

    return workflow_dict

# --- ComfyUI API Interaction ---

async def send_prompt(settings: ComfyUISettings, workflow_dict: Dict[str, Any]) -> Tuple[str, str]:
    """Sends the workflow prompt to ComfyUI."""
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow_dict, "client_id": client_id}
    url = f"{settings.http_url}/prompt"

    logger.info(f"Sending prompt to {url} (Client ID: {client_id})")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status() # Raise exception for bad status codes
                response_data = await response.json()
                prompt_id = response_data.get("prompt_id")
                if not prompt_id:
                     raise ValueError("Prompt ID not found in ComfyUI response")
                logger.success(f"Prompt queued successfully. Prompt ID: {prompt_id}")
                return prompt_id, client_id
    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP Error sending prompt: {e.status} {e.message}")
        logger.error(f"Response: {await e.text()}") # Log response body for debugging
        raise
    except aiohttp.ClientConnectionError as e:
        logger.error(f"Connection error sending prompt: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending prompt: {e}")
        raise


async def listen_for_results(settings: ComfyUISettings, prompt_id: str, client_id: str):
    """Listens to WebSocket using rich.Live for updating display."""
    ws_url = f"{settings.ws_url}?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")

    # --- Rich Live Display Setup ---
    latest_preview_renderable = None
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]Generating: [/]{task.description}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        TimeElapsedColumn(),
        "•",
        TimeRemainingColumn(),
        # TextColumn("[yellow]{task.fields[node]}"), # Example: add node field later
        transient=False, # Keep progress bar after completion for review
    )
    progress_task_id = None # Will be set when first progress message arrives

    # Status text line
    status_text = Text("Connecting...", style="dim")

    def make_renderable() -> Group:
        """Creates the renderable Group for the Live display."""
        items = []
        if latest_preview_renderable:
            items.append(latest_preview_renderable)
            items.append("") # Add a blank line for spacing
        items.append(progress)
        items.append(status_text)
        return Group(*items)

    # The Live context manager - using crop_above to keep progress bar visible
    # while cropping preview image from top if it exceeds terminal height
    with Live(make_renderable(), refresh_per_second=5, vertical_overflow="crop_above") as live:
        try:
            async with websockets.connect(ws_url, ping_interval=10, ping_timeout=30) as ws:
                status_text.plain = "WebSocket connected. Waiting for messages..."
                live.update(make_renderable()) # Initial update

                async for message in ws:
                    if isinstance(message, str):
                        try:
                            data = json.loads(message)
                            msg_type = data.get('type', 'unknown')

                            if msg_type == 'status':
                                status_data = data.get('data', {}).get('status', {})
                                exec_info = status_data.get('exec_info', {})
                                queue_remaining = exec_info.get('queue_remaining', 0)
                                status_text.plain = f"Queue status: {queue_remaining} remaining"

                            elif msg_type == 'progress':
                                progress_data = data.get('data', {})
                                value = progress_data.get('value', 0)
                                max_val = progress_data.get('max', 0)
                                if max_val > 0:
                                    if progress_task_id is None:
                                        # Add task only once
                                        progress_task_id = progress.add_task("", total=max_val, node="") # Add node field
                                    # Update progress (safe even if task_id is None initially)
                                    progress.update(progress_task_id, completed=value, description="") # Clear description for now

                            elif msg_type == 'executing':
                                exec_data = data.get('data', {})
                                node_id = exec_data.get('node')
                                current_prompt_id = exec_data.get('prompt_id')

                                if current_prompt_id == prompt_id:
                                    if node_id is None: # End of execution for this prompt
                                        status_text.plain = f"Execution finished for prompt ID: {prompt_id}"
                                        if progress_task_id is not None and not progress.tasks[0].finished:
                                             progress.update(progress_task_id, completed=progress.tasks[0].total, description="Done")
                                        break # Exit the message loop
                                    else:
                                        # Update status/progress description with current node
                                        status_text.plain = f"Executing node: {node_id or '...'}"
                                        if progress_task_id is not None:
                                            progress.update(progress_task_id, description=f"Node {node_id}")

                            elif msg_type == 'execution_error':
                                error_data = data.get('data', {})
                                node_info = f"Node {error_data.get('node_id')} ({error_data.get('node_type')})"
                                error_msg = error_data.get('exception_message', 'Unknown error')
                                status_text.plain = f"Error: {node_info} - {error_msg}"
                                logger.error(f"Execution Error: {error_data}") # Log full error
                                if progress_task_id is not None:
                                     progress.stop_task(progress_task_id)
                                # Consider breaking or allowing user action on error

                            # Add other message type handlers if needed...

                        except json.JSONDecodeError:
                            logger.warning(f"Received invalid JSON: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}")
                            status_text.plain = f"Error processing message: {e}"

                    elif isinstance(message, bytes):
                        # Handle preview image
                        image_data = message[8:]
                        if image_data:
                            logger.debug(f"Received preview image ({len(image_data)} bytes)")
                            # Get the renderable (term_image object or Text)
                            preview = await get_preview_renderable(image_data)
                            if preview:
                                latest_preview_renderable = preview
                                # Live display will update on next refresh cycle
                        else:
                            logger.debug("Received empty binary message.")

                    # Update the live display explicitly after handling a message
                    live.update(make_renderable())

        except websockets.exceptions.ConnectionClosedOK:
            status_text.plain = "WebSocket connection closed normally."
            logger.info("WebSocket connection closed normally.")
        except websockets.exceptions.ConnectionClosedError as e:
            status_text.plain = f"WebSocket connection closed with error: {e.code}"
            logger.error(f"WebSocket connection closed error: {e}")
        except ConnectionRefusedError:
            status_text.plain = f"Connection refused at {settings.ws_url}"
            logger.error("WebSocket connection refused.")
        except Exception as e:
            status_text.plain = f"WebSocket error: {e}"
            logger.error(f"WebSocket error: {e}", exc_info=True)
        finally:
            # Ensure progress stops cleanly if loop exits unexpectedly
            if progress_task_id is not None and not progress.tasks[0].finished:
                progress.stop_task(progress_task_id)
            # Final update to show final status text
            live.update(make_renderable())
            logger.info("WebSocket listener finished.")

    # Live display stops automatically here
    console.print(f"Final status: {status_text.plain}", style="bold") # Print final status after Live exits


async def fetch_and_save_final_images(settings: ComfyUISettings, prompt_id: str, evaluated_prompt: str = None) -> List[str]:
    """Fetches history, finds final images, downloads, and saves them."""
    history_url = f"{settings.http_url}/history/{prompt_id}"
    logger.info(f"Fetching execution history for prompt ID: {prompt_id}")
    saved_image_paths = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(history_url) as response:
                response.raise_for_status()
                history_data = await response.json()

        if prompt_id not in history_data:
            logger.warning(f"Prompt ID {prompt_id} not found in history.")
            logger.debug(f"Available history keys: {list(history_data.keys())}")
            return []

        prompt_history = history_data[prompt_id]
        outputs = prompt_history.get("outputs", {})

        if not outputs:
            logger.warning(f"No outputs found in history for prompt ID: {prompt_id}")
            return []

        logger.debug(f"Found {len(outputs)} output nodes in history.")
        os.makedirs("images", exist_ok=True)

        images_found = False
        for node_id, node_output in outputs.items():
            if 'images' in node_output:
                for i, image_info in enumerate(node_output['images']):
                    filename = image_info.get("filename")
                    subfolder = image_info.get("subfolder", "")
                    img_type = image_info.get("type", "output") # Usually 'output' or 'temp'

                    if not filename:
                        logger.warning(f"Node {node_id} image {i+1} has missing filename. Skipping.")
                        continue

                    images_found = True
                    logger.info(f"Found final image in node {node_id}: {filename} (Type: {img_type})")

                    # Construct view URL
                    view_url = f"{settings.http_url}/view"
                    params = {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": img_type
                    }

                    try:
                        logger.debug(f"Downloading image: {filename}")
                        async with aiohttp.ClientSession() as img_session:
                            async with img_session.get(view_url, params=params) as img_response:
                                img_response.raise_for_status()
                                image_content = await img_response.read()

                        final_filepath = os.path.join("images", filename)
                        with open(final_filepath, "wb") as f:
                            f.write(image_content)
                        logger.success(f"Final image saved: {final_filepath} ({len(image_content)} bytes)")
                        saved_image_paths.append(final_filepath)
                        
                        # Save the evaluated prompt to a text file with the same name
                        if evaluated_prompt:
                            # Get the filename without extension
                            file_base = os.path.splitext(filename)[0]
                            prompt_filepath = os.path.join("images", f"{file_base}.txt")
                            with open(prompt_filepath, "w", encoding="utf-8") as f:
                                f.write(evaluated_prompt)
                            logger.success(f"Prompt saved: {prompt_filepath}")
                            console.print(f"[green]Prompt saved:[/] {prompt_filepath}")

                    except aiohttp.ClientResponseError as img_err:
                         logger.error(f"HTTP Error downloading image {filename}: {img_err.status} {img_err.message}")
                    except Exception as img_err:
                         logger.error(f"Failed to download or save image {filename}: {img_err}")


        if not images_found:
            logger.warning(f"No images found in any output nodes for prompt ID: {prompt_id}")

    except aiohttp.ClientResponseError as e:
        logger.error(f"HTTP Error fetching history: {e.status} {e.message}")
        logger.error(f"Response: {await e.text()}")
    except aiohttp.ClientConnectionError as e:
        logger.error(f"Connection error fetching history: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to parse history JSON response.")
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching/saving final images: {e}")

    return saved_image_paths