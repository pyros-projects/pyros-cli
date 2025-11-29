"""CLI utility functions for rich console output."""

from rich.console import Console
from art import text2art

console = Console()


def banner_text():
    """Display the CLI banner."""
    console.clear()
    
    test = text2art("Pyro's CLI", font="tarty4")
    console.print(test, style="green")
    text = text2art("**Generating images with style**", font="handwriting1")
    console.print(text, style="green")
    console.line(1)


def print_header(text: str) -> None:
    """Print a header with decorative borders."""
    console.print(f"\n[bold blue]{'═' * 50}[/bold blue]")
    console.print(f"[bold blue]{text}[/bold blue]")
    console.print(f"[bold blue]{'═' * 50}[/bold blue]\n")


def print_subheader(text: str) -> None:
    """Print a subheader."""
    console.print(f"\n[bold cyan]{text}[/bold cyan]")
    console.print(f"[cyan]{'─' * len(text)}[/cyan]")


def print_success(text: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗ Error:[/bold red] {text}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]⚠ Warning:[/bold yellow] {text}")
