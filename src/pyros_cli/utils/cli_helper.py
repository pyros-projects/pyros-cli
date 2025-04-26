"""Banner utilities module."""

from rich.console import Console
from art import text2art



def banner_text():
    """Display the CLI banner."""
    console = Console()
    console.clear()
    
    test = text2art("Pyro's CLI", font="tarty4")
    console.print(test, style="green")
    text = text2art("**Generating images with style**", font="handwriting1")
    console.print(text, style="green")
    console.line(1)
