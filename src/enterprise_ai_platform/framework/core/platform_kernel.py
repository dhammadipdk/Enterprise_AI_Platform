"""
Platform Kernel.

The Platform Kernel is the central runtime coordinator of the
Enterprise AI Platform.
"""

from rich.console import Console


class PlatformKernel:
    """
    Core runtime of the Enterprise AI Platform.
    """

    def __init__(self) -> None:
        self._console = Console()
        self._running = False

    @property
    def is_running(self) -> bool:
        """Return the current running state."""

        return self._running

    def start(self) -> None:
        """
        Start the platform runtime.
        """

        self._console.print("[cyan]Loading configuration...[/cyan]")
        self._console.print("[cyan]Initializing logging...[/cyan]")

        self._running = True

        self._console.print("[green]Platform bootstrap complete.[/green]")

    def stop(self) -> None:
        """
        Stop the platform runtime.
        """

        self._running = False

        self._console.print("[yellow]Platform stopped.[/yellow]")