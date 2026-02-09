"""DeepWork - Framework for enabling AI agents to perform complex, multi-step work tasks."""

__version__ = "0.7.0"
__author__ = "DeepWork Contributors"

__all__ = [
    "__version__",
    "__author__",
]


# Lazy imports to avoid circular dependencies and missing modules during development
def __getattr__(name: str) -> object:
    """Lazy import for core modules."""
    if name in ("JobDefinition", "ParseError", "Step", "StepInput", "parse_job_definition"):
        from deepwork.core.parser import (
            JobDefinition,
            ParseError,
            Step,
            StepInput,
            parse_job_definition,
        )

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
