# Pyros CLI - Project Overview

## Purpose
Pyros CLI is a command-line interface tool designed to facilitate text-to-image generation using ComfyUI's REST API. It provides a streamlined experience for prompt engineering and image generation without requiring direct interaction with ComfyUI's web interface, allowing users to generate and explore amazing prompts with just their keyboard.

## Key Features
- Interactive prompt engineering with command autocompletion
- Configurable connection to ComfyUI backend
- Support for virtually any ComfyUI workflow (images, videos, etc.)
- Dynamic prompt generation with variables
- Command system for special operations
- Multi-image batch generation
- Image preview and gallery functionalities
  - Web-based interactive gallery with responsive layout
  - Full-screen image viewing with prompt text display
  - Background server that allows continued CLI usage
- Session-based prompt history
- Optional AI-enhanced prompt creation (with Ollama, OpenAI, Anthropic, Groq, Gemini)

## Target Users
- AI image generation artists who prefer keyboard-based CLI workflows
- Users who dislike ComfyUI's node-based interface but want its capabilities
- Prompt engineers who want to quickly iterate through prompt variations
- Users who want to batch generate images with similar prompt variations

## High-Level Architecture
Pyros CLI follows a modular design with clear separation of concerns:

1. **CLI Interface** - Main entry point handling user interactions
2. **Configuration Management** - Settings persistence and connection verification
3. **Workflow Management** - Loading and manipulating ComfyUI workflow files
4. **Prompt Processing** - Evaluation, variable substitution, and command handling
5. **ComfyUI API Integration** - Communication with ComfyUI server
6. **Image Handling** - Saving, viewing, and organizing generated images

## Workflow
1. User configures connection to ComfyUI server and workflow
2. User provides a base prompt or modifies an existing one
3. The system evaluates the prompt, processes commands, and substitutes variables
4. The prompt is sent to ComfyUI along with workflow configuration
5. Real-time progress is displayed during generation
6. The final image is saved and optionally displayed
7. User can iterate with the same prompt, an evaluated prompt, or generate multiple images

## Main Features
- **Dynamic Prompts** - Use prompt variables with the `__variable__` syntax for random substitution
- **Batch Generation** - Generate multiple images with the same or varying prompts
- **AI Enhancement** - Optional features to use AI models to enhance prompts or create variations (in progress)
- **Command System** - Slash commands (like `/help`) for various operations
- **Gallery System** - Web-based gallery for browsing and viewing generated images with their prompts

## Dependencies
- ComfyUI server (must be running separately)
- Python 3.8+ runtime environment
- Terminal with good color support
- Various Python libraries (questionary, rich, aiohttp, websockets, etc.) 