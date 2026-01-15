# Identify Fruits

## Objective

Filter the provided list of items to identify only the fruits.

## Task

Given the input `{{raw_items}}`, create a markdown file listing only the items that are fruits.

### Common Fruits Reference

The following are considered fruits:
- **Citrus**: orange, lemon, lime, grapefruit, tangerine, mandarin
- **Berries**: strawberry, blueberry, raspberry, blackberry, cranberry
- **Tropical**: banana, mango, pineapple, papaya, coconut, kiwi
- **Stone fruits**: peach, plum, cherry, apricot, nectarine
- **Pome fruits**: apple, pear, quince
- **Melons**: watermelon, cantaloupe, honeydew
- **Grapes**: grape, raisin

### Instructions

1. Parse the comma-separated list of items
2. For each item, determine if it is a fruit
3. Create a list of only the fruits found

## Output Format

Create `identified_fruits.md` with the following format:

```markdown
# Identified Fruits

The following fruits were identified from the input list:

- [fruit1]
- [fruit2]
- [fruit3]
...

## Summary

Found X fruits from Y total items.
```

## Example

If input is: `apple, car, banana, chair, orange, table`

Output should be:
```markdown
# Identified Fruits

The following fruits were identified from the input list:

- apple
- banana
- orange

## Summary

Found 3 fruits from 6 total items.
```
