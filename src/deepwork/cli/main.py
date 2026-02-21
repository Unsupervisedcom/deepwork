"""DeepWork CLI entry point."""

import click


@click.group()
@click.version_option(package_name="deepwork")
def cli() -> None:
    """DeepWork - Framework for AI-powered multi-step workflows."""
    pass


# Import commands
from deepwork.cli.hook import hook  # noqa: E402
from deepwork.cli.serve import serve  # noqa: E402

cli.add_command(hook)
cli.add_command(serve)


if __name__ == "__main__":
    cli()
