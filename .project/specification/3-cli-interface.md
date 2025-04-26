# CLI Interface

## Interface Overview
Pyros CLI provides an interactive command-line interface focused on streamlining the prompt engineering process for AI image generation. The interface is built using the `questionary` and `rich` libraries to provide a user-friendly experience with features like autocompletion, visual progress tracking, and color-coded output.

## CLI Design

### Banner and Header
- Application displays a stylized banner using ASCII art from the `art` library
- The CLI displays "Pyro's CLI" and "Generating images with style" in green
- Configuration status with current host, port, and workflow settings is shown
- Header sections clearly separate different parts of the interface

### Progress Display
- Real-time generation progress with rich visual components:
  - Spinner animation
  - Progress bar with percentage
  - Time elapsed counter
  - Estimated time remaining
  - Status messages showing current node being processed
- Multi-image generation tracking with individual progress for each image

### Prompt Input
The prompt input system is implemented in the `PromptCompleter` class and provides:
- Text input field with:
  - Command autocompletion (via `/` prefix)
  - Variable autocompletion (via `__` prefix and suffix)
  - Default prompt restoration
- Custom completion that works anywhere in the prompt text (not just at the beginning)
- Intelligent detection of completion context (commands vs. variables)

### Action Selection
After generation completes, users select the next action from a questionary menu:
- "Continue with base prompt" - Keep the original prompt but generate a new image
- "Continue with evaluated prompt" - Use the processed prompt as the new base
- "Regenerate Base Prompt" - Generate multiple images with the same base prompt
- "Regenerate Evaluated Prompt" - Generate multiple images with the same evaluated prompt
- "Quit" - Exit the application

For regeneration options, users can specify how many images to create in batch.

### Seed Control
- Random seed generation for each image (using Python's random module)
- Option to keep the same seed for consistent results
- Seed value is logged for reproducibility

## Technical Implementation

### Main Loop Structure
The CLI is implemented as an asynchronous loop in `start_cli()`:
1. Display banner and header
2. Load or configure settings
3. Load workflow
4. Enter main prompt loop:
   - Get user input
   - Process commands and variables
   - Generate images
   - Show results
   - Present action selection
   - Repeat based on user choice

### Autocomplete System
The autocomplete system is implemented in the `PromptCompleter` class:
```python
class PromptCompleter(Completer):
    def __init__(self, choices):
        self.choices = choices
        self.commands = [cmd[1:] if cmd.startswith('/') else cmd for cmd in choices if cmd.startswith('/')]
        self.vars = [var for var in choices if not var.startswith('/')]
    
    def get_completions(self, document, complete_event):
        # Detect command completions (after /)
        # Detect variable completions (after __)
        # Return appropriate completions
```

Features:
- Detects command patterns starting with `/`
- Detects variable patterns starting with `__`
- Shows context-appropriate suggestions
- Works from any position in the text

### Console Output
Rich console output featuring:
- Color-coded messages by type (error, success, info)
- Progress visualization using Rich's Progress component
- Live updating display with image previews (if supported)
- Clear section headers and formatting

### Session Flow
1. Configuration verification/setup via `check_connection()` and `prompt_for_config()`
2. Prompt input via questionary with custom autocompletion
3. Generation with real-time progress display via `listen_for_results()`
4. Result display with option to view images via `display_final_image_os()`
5. Next action selection via questionary select
6. Repeat or exit based on user choice

## Error Handling
- Connection issues to ComfyUI are detected and reported
- Workflow file errors are identified with clear error messages
- Invalid configurations are flagged with guidance on correction
- Generation errors are displayed with context about the failing node
- Clean exit on keyboard interrupt (Ctrl+C) 