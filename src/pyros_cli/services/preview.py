# preview.py
import asyncio
import contextlib
import io
import os
import platform
import subprocess
from typing import Optional, Union, TYPE_CHECKING

from PIL import Image
from loguru import logger
from rich.text import Text
from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment


# Try importing term-image
# Try importing term-image
try:
    from term_image.image import AutoImage, BaseImage
    TERM_IMAGE_SUPPORTED = True
except ImportError:
    # Log the warning, but don't assign BaseImage = None here yet
    logger.warning("`term-image` library not found. Terminal previews will be disabled.")
    logger.warning("Install with: pip install term-image")
    TERM_IMAGE_SUPPORTED = False
except Exception as e:
    logger.warning(f"Could not initialize `term-image` ({e}). Terminal previews disabled.")
    TERM_IMAGE_SUPPORTED = False

# Assign BaseImage only if import succeeded, otherwise keep it undefined for now
if TERM_IMAGE_SUPPORTED:
    from term_image.image import BaseImage
else:
    BaseImage = None # Now assign None if import failed

_terminal_supports_images: Optional[bool] = None

if TYPE_CHECKING:
    # Allow type checkers to see the real type if available
    if TERM_IMAGE_SUPPORTED:
        pass

# --- NEW Wrapper Class ---
class TermImageRenderable:
    """A rich-compatible wrapper for term-image objects."""
    def __init__(self, term_image_obj: 'BaseImage'):
        if TERM_IMAGE_SUPPORTED:
            if not isinstance(term_image_obj, BaseImage):
                raise TypeError(f"Internal Error: Expected a term_image BaseImage object, got {type(term_image_obj)}")
        elif term_image_obj is not None:
             raise TypeError("Internal Error: Received an object for TermImageRenderable when term-image is not supported.")
        self.term_image_obj = term_image_obj

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        # Capture the output of term_image's draw method
        # --- This part remains the same ---
        with io.StringIO() as buffer:
            target_stdout = console.file if console.is_terminal else buffer
            with contextlib.redirect_stdout(target_stdout):
                 try:
                    # Use the stored object
                    self.term_image_obj.draw()
                 except Exception as e:
                      yield Text(f"[Error drawing preview: {e}]", style="red")
                      return

            captured_output = buffer.getvalue() if target_stdout == buffer else ""
            if captured_output:
                 yield Text(captured_output)
            elif target_stdout != buffer:
                 yield Segment("")

def does_terminal_support_images() -> bool:
    """Checks if the current terminal likely supports image display."""
    # --- Explicitly use the global variable ---
    global _terminal_supports_images

    # Check cache first
    if _terminal_supports_images is not None:
        logger.trace(f"Terminal support already cached: {_terminal_supports_images}")
        return _terminal_supports_images

    logger.debug("Checking terminal image support...")
    support_result = False # Default to False

    if not TERM_IMAGE_SUPPORTED:
        logger.debug("term-image library not available. Disabling previews.")
        support_result = False
    else:
        try:
            logger.trace("Attempting AutoImage test...")
            img = Image.new('RGB', (1, 1))
            AutoImage(img) # This performs the check
            logger.info("Terminal appears to support image previews.")
            support_result = True
        except Exception as e:
            logger.warning(f"Terminal image support check failed ({e}). Disabling previews.")
            support_result = False

    # --- Assign to the global variable ---
    _terminal_supports_images = support_result
    logger.debug(f"Terminal support check complete. Result: {_terminal_supports_images}")
    return _terminal_supports_images

async def display_terminal_preview(image_bytes: bytes):
    """Displays an image preview in the terminal if supported."""
    if not does_terminal_support_images():
        return # Skip if terminal doesn't support images

    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Run PIL operations (like resize if needed) here, before term-image

        # Use asyncio.to_thread to run the potentially blocking term-image display
        def _display():
            img = AutoImage(image)
            # Set preview size - larger = more detail with BlockImage rendering
            img.set_size(width=80)
            print("\n--- Preview ---")
            img.draw()
            print("---------------\n")

        await asyncio.to_thread(_display)
        logger.debug("Terminal preview displayed.")

    except Exception as e:
        # Handle errors during display (e.g., terminal incompatibility detected by term-image)
        logger.warning(f"Could not display terminal preview: {e}")
        # Disable further attempts if it fails consistently
        global _terminal_supports_images
        _terminal_supports_images = False

# Modify get_preview_renderable to use the wrapper
async def get_preview_renderable(image_bytes: bytes) -> Optional[Union[TermImageRenderable, Text]]: # Return type changed
    """
    Processes image bytes and returns a rich-renderable object (TermImageRenderable or Text).
    Returns None if processing fails.
    """
    if not image_bytes:
        return None

    if not does_terminal_support_images():
        return Text("[Preview images disabled]", style="italic dim")

    try:
        image = Image.open(io.BytesIO(image_bytes))

        def _process_image():
            term_image_obj = AutoImage(image)
            # Set preview size - larger = more detail with BlockImage rendering
            # 80 columns gives good detail while fitting most terminal widths
            term_image_obj.set_size(width=80)
            # Wrap the term_image object in our renderable class
            return TermImageRenderable(term_image_obj)

        renderable = await asyncio.to_thread(_process_image)
        logger.debug("Created terminal image renderable wrapper.")
        return renderable

    except Exception as e:
        logger.warning(f"Could not create terminal preview renderable: {e}")
        return Text("[Error processing preview]", style="red")


def display_final_image_os(image_path: str):
    """Opens the final image using the default OS viewer."""
    if not os.path.exists(image_path):
        logger.error(f"Final image not found at path: {image_path}")
        return

    logger.info(f"Attempting to open final image: {image_path}")
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(image_path)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", image_path], check=True, stderr=subprocess.DEVNULL)
        else:  # Linux and other Unix-like (including WSL2)
            # Suppress stderr to avoid D-Bus noise in WSL2 environments
            subprocess.Popen(
                ["xdg-open", image_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent process
            )
        logger.success("Final image opened in default viewer.")
    except FileNotFoundError:
        logger.error(f"Command not found to open image viewer ('open' or 'xdg-open'). Please open manually: {image_path}")
    except Exception as e:
        logger.error(f"Failed to open image with OS default viewer: {e}")
        logger.warning(f"Please open the image manually: {image_path}")