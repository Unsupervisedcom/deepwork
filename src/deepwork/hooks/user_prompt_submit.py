#!/usr/bin/env python3
"""
user_prompt_submit.py - Runs on every user prompt submission.

This is the cross-platform Python equivalent of user_prompt_submit.sh.

This hook captures the work tree state at each prompt submission.
This baseline is used for policies with compare_to: prompt to detect
what changed during an agent response.
"""

from __future__ import annotations

import sys

from deepwork.hooks.capture_prompt import main as capture_prompt_main


def main() -> int:
    """Main entry point for user_prompt_submit hook."""
    # Capture work tree state at each prompt for compare_to: prompt policies
    result = capture_prompt_main()

    # Exit successfully - don't block the prompt
    # Even if capture fails, we don't want to block the user
    return 0 if result == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
