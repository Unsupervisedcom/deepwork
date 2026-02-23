Review this markdown file as a prompt or instruction file, evaluating it against Anthropic's prompt engineering best practices.

For each issue found, report:
1. Location (section or line)
2. Severity (Critical / High / Medium / Low)
3. Best practice violated
4. Description of the issue
5. Suggested improvement

## Best practices to check

**Clarity and specificity**
- Are instructions clear and unambiguous?
- Does it avoid vague language ("do a good job", "be thorough") in favor of concrete criteria?
- Are success criteria or expected outputs explicitly defined?

**Structure and formatting**
- Does it use XML tags, headers, or numbered lists to organize distinct sections?
- Are long prompts broken into logical sections (context, instructions, output format, examples)?
- Is there a clear separation between context, instructions, and constraints?

**Role and context**
- If a system role is appropriate, is one established?
- Is enough context provided for the AI to understand the task without guessing?
- Are assumptions stated explicitly rather than left implicit?

**Examples**
- For complex or nuanced tasks, are examples (few-shot) provided?
- Do examples cover both typical and edge cases where appropriate?

**Output format**
- Is the expected output format specified (e.g., JSON, markdown, bullet list)?
- Are length or scope constraints given where appropriate?

**Prompt anti-patterns**
- Does it avoid contradictory instructions?
- Does it avoid instruction overload (too many competing priorities without ranking)?
- Does it avoid burying critical instructions deep in a wall of text?
- Does it avoid relying on the AI to infer important constraints?

**Variable and placeholder usage**
- Are dynamic inputs clearly marked with placeholders or template variables?
- Is it clear what each variable represents?

## Judgment

Not every file needs every best practice. Use your judgment — a short, focused instruction for a simple task does not need few-shot examples or XML tags. Evaluate proportionally to the complexity and ambiguity of the task the prompt is trying to accomplish. Do not flag issues for best practices that are irrelevant to the file's purpose.
