# Compound Learnings

Document recently solved problems to compound team knowledge.

## Purpose

This step captures problem solutions while context is fresh, creating structured documentation for future reference. Each documented solution compounds your team's knowledge.

**Why "compound"?**: The first time you solve a problem takes research. Document it, and the next occurrence takes minutes. Knowledge compounds.

**The feedback loop**:
```
Build -> Test -> Find Issue -> Research -> Improve -> Document -> Validate -> Deploy
  ^                                                                             |
  +-----------------------------------------------------------------------------+
```

## Input

**Context** (optional): `{{context}}`

Brief description of what was fixed. If not provided, extract from recent conversation.

## When to Use

**Use when**:
- A non-trivial problem was just solved
- Multiple investigation attempts were needed
- The solution wasn't obvious
- Future sessions would benefit from documentation

**Skip when**:
- Simple typo fixed
- Obvious syntax error
- Trivial fix immediately corrected

## Execution Flow

### Phase 1: Gather Context

Extract from the conversation or work just completed:

**Required information**:
- **Module/Component**: Which part of the system had the problem?
- **Symptom**: What was the observable error/behavior?
- **Investigation Steps**: What didn't work and why?
- **Root Cause**: Technical explanation of the actual problem
- **Solution**: What fixed it (code/config changes)
- **Prevention**: How to avoid this in future

**If context is missing**, ask:
> "I'd like to document this solution for future reference. Can you tell me:"
> 1. Which module/component was affected?
> 2. What was the exact error or symptom?
> 3. What solution worked?

Do not proceed until critical context is gathered.

### Phase 2: Check Existing Documentation

Search for similar documented issues:

```bash
# Search by keywords
grep -r "error message keywords" docs/solutions/ 2>/dev/null

# List recent solutions
ls -lt docs/solutions/*/*.md 2>/dev/null | head -10
```

**If similar issue found**:
> "Found similar issue: `docs/solutions/[path]`"
> 1. **Create new doc with cross-reference** (recommended if different root cause)
> 2. **Update existing doc** (if same root cause, new variation)
> 3. **Skip documentation** (if already covered)

### Phase 3: Categorize the Problem

Determine the appropriate category based on problem type:

| Problem Type | Category Folder |
|-------------|-----------------|
| Build/compile errors | `build-errors/` |
| Test failures | `test-failures/` |
| Runtime errors | `runtime-errors/` |
| Performance issues | `performance-issues/` |
| Database issues | `database-issues/` |
| Security issues | `security-issues/` |
| UI/UX bugs | `ui-bugs/` |
| Integration issues | `integration-issues/` |
| Logic errors | `logic-errors/` |

### Phase 4: Create Documentation

#### 4.1 Generate Filename

Format: `[symptom-slug]-[module]-[YYYYMMDD].md`

Examples:
- `n-plus-one-query-briefs-20260129.md`
- `missing-include-email-processor-20260129.md`
- `webview-crash-on-resize-assistant-20260129.md`

#### 4.2 Create the Document

```bash
mkdir -p docs/solutions/[category]
```

**Template**:

```markdown
---
module: [Module Name]
date: YYYY-MM-DD
problem_type: [build_error|test_failure|runtime_error|performance_issue|database_issue|security_issue|ui_bug|integration_issue|logic_error]
severity: [critical|high|medium|low]
symptoms:
  - "Exact error message or symptom 1"
  - "Observable behavior 2"
tags: [relevant, tags, here]
---

# [Brief Problem Title]

## Symptom
[What we observed - exact error messages, unexpected behavior]

```
[Paste exact error output if applicable]
```

## Investigation
### What We Tried
1. **[First attempt]**: [What we tried and why it didn't work]
2. **[Second attempt]**: [What we tried and why it didn't work]

### Root Cause
[Technical explanation of why the problem occurred]

## Solution
[Step-by-step what fixed it]

### Code Changes
```[language]
# Before
[problematic code]

# After
[fixed code]
```

## Prevention
- [ ] [How to avoid this in the future]
- [ ] [Tests or checks to add]
- [ ] [Documentation to update]

## Related Issues
- [Link to similar docs if any]
- [Related PR or issue if applicable]

## Time Spent
- Investigation: ~[X] minutes
- Fix: ~[X] minutes
- Documentation: ~[X] minutes
```

### Phase 5: Post-Documentation Options

After creating the document, present options:

> "Solution documented at `docs/solutions/[category]/[filename].md`"
>
> What's next?
> 1. **Continue workflow** - Documentation complete
> 2. **Add to Required Reading** - Promote to critical patterns (for recurring issues)
> 3. **Link related issues** - Connect to similar problems
> 4. **View documentation** - Review what was captured
> 5. **Other** - Specify

**Option 2: Add to Required Reading**

For critical patterns that should always be followed:

```bash
mkdir -p docs/solutions/patterns

# Add to critical patterns file
cat >> docs/solutions/patterns/critical-patterns.md << 'EOF'

## [Pattern Number]: [Pattern Name]

**Context**: [When this applies]

**Wrong** (don't do this):
```[language]
[anti-pattern code]
```

**Right** (do this instead):
```[language]
[correct pattern code]
```

**Why**: [Explanation]

**See also**: [Link to full solution doc]
EOF
```

## Quality Guidelines

**Good documentation includes**:
- Exact error messages (copy-paste from output)
- Specific file:line references
- Observable symptoms (what you saw, not interpretations)
- Failed attempts documented (helps avoid wrong paths)
- Technical explanation (not just "what" but "why")
- Code examples (before/after if applicable)
- Prevention guidance (how to catch early)
- Cross-references (related issues)

**Avoid**:
- Vague descriptions ("something was wrong")
- Missing technical details ("fixed the code")
- No context (which version? which file?)
- Just code dumps (explain why it works)
- No prevention guidance
- No cross-references

## Example

**User**: "That worked! The N+1 query is fixed."

**Document created**: `docs/solutions/performance-issues/n-plus-one-brief-generation-20260129.md`

```markdown
---
module: Brief System
date: 2026-01-29
problem_type: performance_issue
severity: high
symptoms:
  - "Brief generation taking >5 seconds"
  - "N+1 query when loading email threads"
tags: [n-plus-one, eager-loading, performance, rails]
---

# N+1 Query in Brief Generation

## Symptom
Brief generation was taking >5 seconds with visible N+1 queries in logs:
```
SELECT * FROM emails WHERE brief_id = 1
SELECT * FROM emails WHERE brief_id = 2
...
```

## Investigation
### What We Tried
1. **Added pagination**: Didn't help - still N+1 per page
2. **Background job**: Masked symptom but didn't fix root cause

### Root Cause
Missing eager loading on the Brief model's email association. Each brief was triggering a separate query for its emails.

## Solution
Added `includes(:emails)` to the Brief query.

### Code Changes
```ruby
# Before
@briefs = Brief.where(user: current_user)

# After
@briefs = Brief.where(user: current_user).includes(:emails)
```

## Prevention
- [ ] Add bullet gem to catch N+1 queries in development
- [ ] Review queries when adding new associations
- [ ] Add performance tests for list views
```

## Output

When complete, display:

```
Solution documented!

File: docs/solutions/[category]/[filename].md
Category: [category]
Severity: [severity]

This documentation will be searchable for future reference when similar issues occur.

The Compounding Effect:
- First time solving this: ~[X] minutes research
- Next time with docs: ~2 minutes lookup
- Knowledge compounds!

Next: Continue with your workflow or add to Required Reading if this is a critical pattern.
```
