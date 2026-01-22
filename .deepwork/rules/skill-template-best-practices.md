---
name: Skill Template Best Practices
trigger: src/deepwork/templates/**/skill-job*.jinja
compare_to: prompt
prompt_runtime: send_to_stopping_agent
---
Skill template files are being modified. Ensure the generated skills follow these best practices:

## Description Guidelines

The description appears in skill search results and helps users find the right skill. Keep it search-friendly and scannable.

1. **Be specific** - Name exact capabilities/actions the skill performs
2. **Keep concise** - One sentence, max ~100 chars; describes WHAT it does, not HOW
3. **Avoid vagueness** - "Extract text from PDFs, fill forms" is good; "Helps with documents" is bad
4. **Avoid meta-language** - Don't include "Trigger:", "Keywords:", or similar prefixes. Let the description itself be searchable.

## Instruction Writing

1. **Keep focused** - Core instructions should be under 500 lines; use supporting files for details
2. **Use progressive disclosure** - Essential info in main content, detailed reference in linked files
3. **Be explicit** - Provide clear, step-by-step guidance rather than relying on inference
4. **Structure clearly** - Use headers, numbered lists for sequential steps, bullets for options

## Prompt Structure

1. **Specificity first** - Detailed directions upfront prevent course corrections later
2. **Plan before action** - Ask agent to analyze/plan before implementing
3. **Reference concrete files** - Use specific paths, not general descriptions
4. **Include context** - Mention edge cases, preferred patterns, and expected outcomes

## Quality Criteria

1. **Make measurable** - Criteria should be verifiable, not subjective
2. **Focus on outcomes** - What the output should achieve, not process steps
3. **Keep actionable** - Agent should be able to self-evaluate against criteria

## Platform Considerations

- **Claude**: Supports hooks for automated validation; use Skill tool for step invocation
- **Gemini**: No hook support; instructions must guide manual verification

## Reference Documentation

When unsure about best practices, consult:
- https://code.claude.com/docs/en/skills - Official skills documentation
- https://www.anthropic.com/engineering/claude-code-best-practices - Prompting best practices
