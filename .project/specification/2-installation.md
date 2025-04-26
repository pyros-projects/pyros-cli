# Installation and Setup

## Prerequisites

- A terminal that supports more than two colors
  - `iterm2` on macOS is recommended
  - `Windows Terminal` on Windows is recommended

## Installation

### Install uv

The recommended way to install is using `uv`, a modern package and project manager for Python:

```bash
# First install uv
# See https://docs.astral.sh/uv/getting-started/installation/
```

### Install pyros-cli

Create a new directory, navigate with your terminal into it and run:

```bash
uvx --prerelease=allow pyros-cli
```

That's it!

## Setup

### 1. Open ComfyUI

Start ComfyUI and open your favorite workflow. The type of workflow doesn't matter - it can be for images, videos, or any other output.

In the settings, activate **Dev Mode**.

### 2. Export your workflow

Export your workflow in API mode.

Save it into the directory you created during the installation.

### 3. Getting required node information

To let Pyro's CLI interact with your workflow, you need information about some specific nodes:

- The node where your prompt is defined
- The node which generates the seed
- The node where the amount of steps for generation is set

For each node, note:
- Its ID (usually a number)
- The property name (like "text" for prompt nodes)

### 4. Run Pyro's CLI and configure ComfyUI connection

Start Pyro's CLI with:
```bash
uvx --prerelease=allow pyros-cli
```

Follow the configuration prompts:
- Enter network settings for ComfyUI (defaults should work for local instances)
- Set the path to your exported workflow
- Enter the node IDs and property names you noted in the previous step

Configuration is saved to disk and will be reused in subsequent sessions.

## Configuration File

The configuration is stored in an `.env` file in the directory where Pyros CLI is running.

## Workflow Requirements

For a ComfyUI workflow to be compatible with Pyros CLI:

1. It must contain at least one text prompt node with an input field
2. It must contain a node for setting sampling steps
3. It must contain a node for setting the seed
4. All nodes must have a unique identifier

## Environment Variables

- `LOG_LEVEL`: Sets the logging verbosity (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
- Default: CRITICAL

## Troubleshooting

- Ensure ComfyUI is running and accessible at the configured host/port
- Check that your workflow file exists and has the required nodes
- For connection issues, verify network settings and firewall configurations
- For workflow errors, validate the JSON file against ComfyUI's requirements 