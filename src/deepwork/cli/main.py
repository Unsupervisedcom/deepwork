"""DeepWork CLI entry point."""

import click


@click.group()
@click.version_option(package_name="deepwork")
def cli() -> None:
    """DeepWork - Framework for AI-powered multi-step workflows."""
    pass


# Import commands
from deepwork.cli.hook import hook  # noqa: E402
from deepwork.cli.install import install, sync  # noqa: E402
from deepwork.cli.serve import serve  # noqa: E402

cli.add_command(hook)
cli.add_command(serve)

# DEPRECATION NOTICE: Remove after June 1st, 2026.
# install and sync are hidden back-compat commands that tell users
# to migrate to the Claude plugin distribution model.
cli.add_command(install)
cli.add_command(sync)


if __name__ == "__main__":
    cli()
