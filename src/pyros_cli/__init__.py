import asyncio

from loguru import logger
from rich.console import Console

from pyros_cli.main import start_cli

console = Console()

def main() -> None:
    try:
        asyncio.run(start_cli())
    except KeyboardInterrupt:
        console.print("\nExiting due to user interrupt.", style="bold red")
    except Exception as e:
         # Catch unexpected errors during shutdown or setup
        logger.critical(f"Unhandled exception in main execution: {e}", exc_info=True)
