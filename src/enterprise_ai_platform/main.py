"""
Enterprise AI Platform.

Application entry point.
"""

from rich.console import Console
from rich.panel import Panel

from enterprise_ai_platform.bootstrap.platform_bootstrap import PlatformBootstrap

console = Console()


def main() -> None:
    """
    Main entry point.
    """

    console.print()

    console.print(
        Panel.fit(
            "[bold cyan]Enterprise AI Platform[/bold cyan]\n"
            "Version 1.0.0",
            title="Startup",
        )
    )

    bootstrap = PlatformBootstrap()
    bootstrap.run()

    console.print()
    console.print("[bold green]Platform Ready.[/bold green]")


if __name__ == "__main__":
    main()