"""DeepWork CLI entry point."""

import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option(package_name="deepwork")
def cli() -> None:
    """DeepWork - Framework for AI-powered multi-step workflows."""
    pass


# Import commands
from deepwork.cli.install import install  # noqa: E402

cli.add_command(install)


if __name__ == "__main__":
    cli()
