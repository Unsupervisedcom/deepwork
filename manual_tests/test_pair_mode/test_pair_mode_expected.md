# API Documentation (Pair Mode Expected File)

## What This File Does

This is the "expected" file in a pair mode rule.

## Pair Mode Behavior

- When `test_pair_mode_trigger.py` changes, this file MUST also change
- When THIS file changes alone, NO rule fires (docs can update independently)

## API Reference

### `api_endpoint()`

Returns a status response.

**Returns:** `{"status": "ok", "message": "API response"}`

---

## Testing Instructions

1. To TRIGGER the rule: Edit only `test_pair_mode_trigger.py`
2. To verify ONE-WAY: Edit only this file (rule should NOT fire)
3. To SATISFY the rule: Edit both files together

---

Edit below this line (editing here alone should NOT trigger the rule):
<!-- Changes here -->
