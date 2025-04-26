# ComfyUI API Integration

## Overview
Pyros CLI integrates with ComfyUI's API to submit workflows, track generation progress, and retrieve generated images. This document details the API integration architecture, communication protocols, and data formats as implemented in the `comfy_utils.py` module.

## API Communication Architecture

### HTTP API Endpoints

| Endpoint | Method | Purpose | Request Format | Response Format |
|----------|--------|---------|----------------|-----------------|
| `/prompt` | POST | Submit workflow for generation | JSON | JSON with prompt_id |
| `/history` | GET | Retrieve generation history | N/A | JSON array |
| `/history/{prompt_id}` | GET | Get specific generation details | N/A | JSON object |
| `/view` | GET | Retrieve generated images | Query params | Binary image data |

### WebSocket Communication
- Connection established to: `ws://{host}:{port}/ws?clientId={client_id}`
- Receives real-time status updates and execution progress
- Message types include:
  - `status`: Queue and execution status
  - `progress`: Overall progress percentage
  - `executing`: Node currently executing
  - `executed`: Node execution completed
  - `execution_error`: Error during execution

## API Integration Implementation

### URL Construction
URLs are built using properties from the `ComfyUISettings` class:
```python
# In ComfyUISettings class
@property
def http_url(self):
    return f"http://{self.host}:{self.port}"

@property
def ws_url(self):
     return f"ws://{self.host}:{self.port}/ws"
```

### Workflow Submission
Implemented in the `send_prompt()` function:
```python
async def send_prompt(settings: ComfyUISettings, workflow_dict: Dict[str, Any]) -> Tuple[str, str]:
    """Sends the workflow prompt to ComfyUI."""
    client_id = str(uuid.uuid4())
    payload = {"prompt": workflow_dict, "client_id": client_id}
    url = f"{settings.http_url}/prompt"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            response_data = await response.json()
            prompt_id = response_data.get("prompt_id")
            return prompt_id, client_id
```

1. Generate a unique client ID using UUID
2. Prepare payload with workflow and client ID
3. Send POST request to the `/prompt` endpoint
4. Return prompt ID and client ID for tracking

### Progress Monitoring
Implemented in the `listen_for_results()` function using:
- WebSocket connection to receive real-time updates
- Rich Progress for visual display
- Live updating preview images

```python
async def listen_for_results(settings: ComfyUISettings, prompt_id: str, client_id: str):
    ws_url = f"{settings.ws_url}?clientId={client_id}"
    
    with Live(...) as live:
        async with websockets.connect(ws_url) as ws:
            async for message in ws:
                # Process different message types
                # Update progress display
```

Key features:
- Asynchronous WebSocket connection
- JSON message parsing
- Progress bar with spinner, percentage, and time estimation
- Preview image display (if terminal supports it)
- Detailed status messages

### Image Retrieval
Implemented in the `fetch_and_save_final_images()` function:
```python
async def fetch_and_save_final_images(settings: ComfyUISettings, prompt_id: str, evaluated_prompt: str = None) -> List[str]:
    """Fetches history, finds final images, downloads, and saves them."""
    # Get execution history
    history_url = f"{settings.http_url}/history/{prompt_id}"
    
    # Find image outputs in history
    # For each image:
    #   Construct view URL
    #   Download image
    #   Save to images/ directory
    #   Save prompt text alongside image
```

1. Fetch execution history from `/history/{prompt_id}`
2. Extract image information from output nodes
3. Download each image using `/view` endpoint
4. Save images to disk with metadata
5. Save the prompt text in a companion file
6. Return paths to saved images

## Progress Visualization
The progress display includes:
- Spinner animation
- Text description of current operation
- Progress bar
- Percentage completion
- Elapsed time
- Remaining time estimation
- Current node being processed

## Error Handling

Error handling is implemented throughout the API integration:

### Connection Errors
```python
except aiohttp.ClientConnectionError as e:
    logger.error(f"Connection error sending prompt: {e}")
    raise
```

### API Response Errors
```python
except aiohttp.ClientResponseError as e:
    logger.error(f"HTTP Error sending prompt: {e.status} {e.message}")
    logger.error(f"Response: {await e.text()}")
    raise
```

### WebSocket Errors
```python
except websockets.exceptions.ConnectionClosedError as e:
    status_text.plain = f"WebSocket connection closed with error: {e.code}"
    logger.error(f"WebSocket connection closed error: {e}")
```

### Unexpected Errors
```python
except Exception as e:
    logger.error(f"Unexpected error sending prompt: {e}")
    raise
```

## Security Considerations
- URL validation for API endpoints
- Proper exception handling to prevent information leakage
- Logging with different verbosity levels
- No sensitive data in requests

## Preview Image Support
The system can display preview images in terminals that support it using the `term_image` library:
```python
# Attempt to display terminal preview
if does_terminal_support_images():
    # Process and display the preview image
    latest_preview_renderable = await get_preview_renderable(image_data)
``` 