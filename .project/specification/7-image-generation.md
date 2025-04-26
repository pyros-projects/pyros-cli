# Image Generation Process

## Overview
The image generation process in Pyros CLI orchestrates the communication with ComfyUI, handles the generation workflow, processes intermediate status updates, manages preview images, and handles the final output images. This functionality is primarily implemented in the `comfy_utils.py` and `preview.py` modules.

## Generation Lifecycle

### 1. Preparation
- User submits prompt through CLI
- Prompt evaluation and variable substitution occurs
- Random seed is generated (or reused if specified) using Python's random module
- Workflow JSON is modified with prompt, seed, and any additional properties

### 2. Submission
Implementation in `send_prompt()` function:
```python
async def send_prompt(settings: ComfyUISettings, workflow_dict: Dict[str, Any]) -> Tuple[str, str]:
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow_dict, "client_id": client_id}
    url = f"{settings.http_url}/prompt"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response_data = await response.json()
            prompt_id = response_data.get("prompt_id")
            return prompt_id, client_id
```

- Modified workflow is sent to ComfyUI's API
- A unique client ID is generated for tracking
- The API returns a prompt ID for the queued job
- These IDs are used for further communication

### 3. Progress Monitoring
Implementation in `listen_for_results()` function using Rich's Live display:
```python
async def listen_for_results(settings: ComfyUISettings, prompt_id: str, client_id: str):
    ws_url = f"{settings.ws_url}?clientId={client_id}"
    
    with Live(...) as live:
        async with websockets.connect(ws_url) as ws:
            async for message in ws:
                # Process different message types
                # Update progress display
```

- WebSocket connection established to receive real-time updates
- Progress events are processed and displayed to the user
- Rich progress bar shows completion percentage, elapsed time, and current node
- Preview images may be shown during generation if terminal supports it

### 4. Preview Handling
The system can display preview images in-terminal using the `term_image` library:
```python
async def get_preview_renderable(image_bytes: bytes):
    if does_terminal_support_images():
        image = Image.open(io.BytesIO(image_bytes))
        term_image_obj = AutoImage(image)
        return TermImageRenderable(term_image_obj)
    else:
        return Text("[Preview images disabled]", style="italic dim")
```

- Terminal image support is detected automatically
- Preview images are displayed in the terminal if supported
- Fallback text is shown for terminals without image support

### 5. Completion and Image Retrieval
Implementation in `fetch_and_save_final_images()` function:
```python
async def fetch_and_save_final_images(settings: ComfyUISettings, prompt_id: str, evaluated_prompt: str = None):
    # Get execution history
    history_url = f"{settings.http_url}/history/{prompt_id}"
    
    # Process history to find image outputs
    # Download and save each image
    # Save prompt text alongside image
```

- Execution history is fetched from ComfyUI
- Image outputs are identified in the node results
- Each final image is downloaded and saved to the "images" directory
- The prompt text is saved in a companion file with the same name
- Image paths are returned for viewing

### 6. Post-processing
- Option to view the generated image using the OS's default viewer
- Image metadata is recorded in text files
- Path can be passed to gallery for browsing

## Image Preview Features

### Terminal Preview Support
The system checks for terminal image support using the `term_image` library:
```python
def does_terminal_support_images() -> bool:
    # Check if terminal supports images using term_image
    try:
        img = Image.new('RGB', (1, 1))
        AutoImage(img)
        return True
    except Exception:
        return False
```

- Automatically detects terminal image support capabilities
- Caches the detection result for performance
- Uses the `term_image` library for cross-platform support

### Preview Rendering
The system provides a custom Rich-compatible renderable for terminal previews:
```python
class TermImageRenderable:
    """A rich-compatible wrapper for term-image objects."""
    def __init__(self, term_image_obj: 'BaseImage'):
        self.term_image_obj = term_image_obj

    def __rich_console__(self, console, options):
        # Draw the image in the terminal
```

- Integrates with Rich's console display system
- Allows previews to be part of the Live display
- Handles errors gracefully if rendering fails

## OS-Level Image Viewing
For final image viewing, the system can open the default OS viewer:
```python
def display_final_image_os(image_path: str):
    system = platform.system()
    if system == "Windows":
        os.startfile(image_path)
    elif system == "Darwin":  # macOS
        subprocess.run(["open", image_path], check=True)
    else:  # Linux and other Unix-like
        subprocess.run(["xdg-open", image_path], check=True)
```

- Cross-platform support for Windows, macOS, and Linux
- Uses appropriate system command for each platform
- Reports errors if the viewer can't be launched

## Progress Tracking Visualization
The progress display includes:
- Spinner animation for active processing
- Progress bar showing percentage complete
- Time elapsed counter
- Estimated time remaining
- Current node being processed
- Status text with detailed information
- Preview image (if terminal supports it)

## Error Handling
- Connection issues are caught with specific error types
- Generation errors include node information
- Image saving errors are handled with fallbacks
- Timeout handling for WebSocket connections
- Logger provides detailed error information at different verbosity levels

## Multi-Image Generation
- Option to generate multiple images with the same prompt
- Progress tracking shows current image and total count
- Each image uses a different random seed by default
- Option to keep the same seed for consistency

## API Communication

### REST API Endpoints
- `/prompt` - Submit workflow for generation
- `/view` - Retrieve generated images
- `/history` - Access generation history
- `/upload` - Upload images or other assets

### WebSocket Communication
- Status updates streamed in real-time
- Progress percentage
- Preview image updates
- Error notifications

## Progress Tracking
- Rich progress bar shows generation status
- Spinner indicates active processing
- Time elapsed counter
- Status messages update with current operation
- Batch progress for multi-image generation

## Image Handling

### Saving Format
- Images are saved to an `images` directory by default
- Filename format: `{timestamp}_{prompt_hash}_{seed}.png`
- Original prompt is stored in image metadata or companion file
- Seed value is preserved for reproducibility

### Viewing Images
- Option to open generated images using the system's default viewer
- Gallery mode for browsing multiple generations
- Basic image metadata display

## Performance Considerations
- Asynchronous communication for responsive UI
- Efficient progress updates to minimize bandwidth
- Proper cleanup of connections and resources
- Memory management for large workflows or images

## Multi-Image Generation
- Batched generation request option
- Consistent seed management across batch
- Progress tracking for the entire batch
- Result organization and presentation 