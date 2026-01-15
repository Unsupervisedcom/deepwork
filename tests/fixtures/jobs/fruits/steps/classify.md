# Classify Fruits

## Objective

Organize the identified fruits into categories based on their type.

## Task

Read the `identified_fruits.md` file from the previous step and categorize each fruit.

### Fruit Categories

Use these standard categories:

1. **Citrus** - orange, lemon, lime, grapefruit, tangerine, mandarin, clementine
2. **Berries** - strawberry, blueberry, raspberry, blackberry, cranberry, mulberry
3. **Tropical** - banana, mango, pineapple, papaya, coconut, kiwi, passion fruit
4. **Stone Fruits** - peach, plum, cherry, apricot, nectarine, lychee
5. **Pome Fruits** - apple, pear, quince
6. **Melons** - watermelon, cantaloupe, honeydew, melon
7. **Grapes** - grape, raisin

If a fruit doesn't fit any category, list it under **Other**.

## Output Format

Create `classified_fruits.md` with the following format:

```markdown
# Classified Fruits

## [Category Name]
- [fruit1]
- [fruit2]

## [Another Category]
- [fruit3]

---

## Summary

| Category | Count |
|----------|-------|
| [category1] | X |
| [category2] | Y |
| **Total** | **Z** |
```

## Example

If `identified_fruits.md` contains: apple, banana, orange

Output should be:
```markdown
# Classified Fruits

## Citrus
- orange

## Tropical
- banana

## Pome Fruits
- apple

---

## Summary

| Category | Count |
|----------|-------|
| Citrus | 1 |
| Tropical | 1 |
| Pome Fruits | 1 |
| **Total** | **3** |
```

## Notes

- Only include categories that have at least one fruit
- Sort fruits alphabetically within each category
- Ensure the summary table matches the categorized fruits
