# Manual Test: Claude Runtime
# This file triggers a rule that uses the 'claude' prompt_runtime.
#
# When this file is edited, the rule should:
# 1. Invoke Claude Code in headless mode
# 2. Claude reviews the code and responds with a structured result
# 3. The hook parses Claude's response (block/allow)
#
# To test:
# 1. Edit this file (e.g., add a comment or change the function)
# 2. Run the rules_check hook
# 3. Verify Claude is invoked and returns a structured response


def calculate_sum(numbers: list[int]) -> int:
    """Calculate the sum of a list of numbers."""
    total = 0
    for num in numbers:
        total += num
    return total


def calculate_average(numbers: list[int]) -> float:
    """Calculate the average of a list of numbers."""
    if not numbers:
        return 0.0
    return calculate_sum(numbers) / len(numbers)
