# Manual Test: Claude Runtime
# This file triggers a rule that uses the 'claude' prompt_runtime.
#
# When this file is edited, the rule should:
# 1. Invoke Claude Code in headless mode
# 2. Claude reviews the code and responds with a structured result
# 3. The hook parses Claude's response (block/allow)
#
# To test:
# 1. Introduce a BLATANT ERROR in the code below (e.g., undefined variable,
#    obvious bug like dividing by zero, or completely wrong logic)
# 2. The Claude runtime will invoke Claude Code in headless mode
# 3. Claude should detect the error and return a "block" response
# 4. In Claude Code Web environment, you'll see the fallback prompt instead


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
