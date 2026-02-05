#!/usr/bin/env python3
"""Mock review agent for integration testing.

This script simulates a review agent that reads a prompt from stdin
and returns a JSON response in Claude CLI wrapper format. The behavior
is controlled by environment variables or by keywords in the input prompt.

############################################################################
# CRITICAL: OUTPUT FORMAT
#
# This mock returns responses in the same wrapper format as Claude CLI
# when using `--print --output-format json --json-schema`. The quality gate
# response is in the `structured_output` field:
#
# {
#     "type": "result",
#     "subtype": "success",
#     "is_error": false,
#     "structured_output": {
#         "passed": true/false,
#         "feedback": "...",
#         "criteria_results": [...]
#     }
# }
#
# See doc/reference/calling_claude_in_print_mode.md for details.
############################################################################

Behavior modes:
- REVIEW_RESULT=pass: Always return passed=true
- REVIEW_RESULT=fail: Always return passed=false
- REVIEW_RESULT=malformed: Return invalid JSON
- REVIEW_RESULT=empty: Return empty response
- REVIEW_RESULT=timeout: Sleep forever (for timeout testing)
- REVIEW_RESULT=error: Exit with non-zero code
- Default: Parse prompt and look for FORCE_PASS or FORCE_FAIL markers
"""

import json
import os
import sys
import time


def wrap_response(quality_result: dict) -> dict:
    """Wrap a quality gate result in Claude CLI output format.

    Args:
        quality_result: The quality gate result with passed, feedback, criteria_results

    Returns:
        Wrapper object matching Claude CLI --output-format json --json-schema output
    """
    return {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "structured_output": quality_result,
    }


def main() -> int:
    """Main entry point."""
    mode = os.environ.get("REVIEW_RESULT", "auto")

    # Read prompt from stdin
    prompt = sys.stdin.read()

    if mode == "timeout":
        # Sleep forever to trigger timeout
        time.sleep(3600)
        return 0

    if mode == "error":
        print("Review agent error!", file=sys.stderr)
        return 1

    if mode == "empty":
        return 0

    if mode == "malformed":
        print("This is not valid JSON {{{")
        return 0

    if mode == "pass":
        response = wrap_response(
            {
                "passed": True,
                "feedback": "All criteria met",
                "criteria_results": [
                    {"criterion": "Criterion 1", "passed": True, "feedback": None}
                ],
            }
        )
        print(json.dumps(response))
        return 0

    if mode == "fail":
        response = wrap_response(
            {
                "passed": False,
                "feedback": "Quality criteria not met",
                "criteria_results": [
                    {
                        "criterion": "Criterion 1",
                        "passed": False,
                        "feedback": "Did not meet requirements",
                    }
                ],
            }
        )
        print(json.dumps(response))
        return 0

    # Auto mode: parse prompt for markers
    if "FORCE_PASS" in prompt:
        response = wrap_response(
            {
                "passed": True,
                "feedback": "Forced pass via marker",
                "criteria_results": [],
            }
        )
        print(json.dumps(response))
        return 0

    if "FORCE_FAIL" in prompt:
        response = wrap_response(
            {
                "passed": False,
                "feedback": "Forced fail via marker",
                "criteria_results": [
                    {
                        "criterion": "Test criterion",
                        "passed": False,
                        "feedback": "Failed due to FORCE_FAIL marker",
                    }
                ],
            }
        )
        print(json.dumps(response))
        return 0

    # Default: analyze the prompt for quality criteria and outputs
    # Extract criteria from prompt and evaluate based on output content
    criteria_results = []
    all_passed = True

    # Check if outputs contain expected patterns
    if "File not found" in prompt:
        criteria_results.append(
            {
                "criterion": "Output files must exist",
                "passed": False,
                "feedback": "One or more output files were not found",
            }
        )
        all_passed = False
    elif "Test content" in prompt or "output.md" in prompt:
        criteria_results.append(
            {
                "criterion": "Output files must exist",
                "passed": True,
                "feedback": None,
            }
        )

    # Look for "must contain" type criteria
    if "must contain" in prompt.lower():
        if "expected content" in prompt.lower():
            criteria_results.append(
                {
                    "criterion": "Output must contain expected content",
                    "passed": True,
                    "feedback": None,
                }
            )
        else:
            criteria_results.append(
                {
                    "criterion": "Output must contain expected content",
                    "passed": False,
                    "feedback": "Expected content not found in output",
                }
            )
            all_passed = False

    if not criteria_results:
        # If no specific criteria matched, default based on whether outputs exist
        criteria_results.append(
            {
                "criterion": "General quality check",
                "passed": True,
                "feedback": None,
            }
        )

    quality_result = {
        "passed": all_passed,
        "feedback": "All criteria met" if all_passed else "Some criteria failed",
        "criteria_results": criteria_results,
    }

    print(json.dumps(wrap_response(quality_result)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
