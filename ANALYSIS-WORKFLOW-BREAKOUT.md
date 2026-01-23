# Analysis: Preventing Claude from Breaking Out of DeepWork Workflows

**Date**: 2026-01-23
**Status**: Design Review Needed

---

## Executive Summary

When users invoke `/deepwork_jobs.define` and describe the workflow they want, Claude sometimes interprets their response as a direct command and executes the task instead of designing a workflow for it. This is a **prompt interpretation problem**, not a deliberate escape—Claude misreads workflow descriptions as instructions.

**Recommended fix**: Reframe skill instructions to make Claude's "architect mode" explicit, with clear guidance on interpreting user responses as descriptions rather than commands.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Proposed Solutions](#proposed-solutions)
4. [Sub-Agent Architecture (Future Option)](#sub-agent-architecture-future-option)
5. [Recommended Implementation](#recommended-implementation)
6. [Testing Plan](#testing-plan)
7. [Open Questions](#open-questions)

---

## Problem Statement

### The Scenario

```
1. User: /deepwork_jobs.define

2. Claude (following skill): "What complex task or workflow are you trying to accomplish?"

3. User: "Can you research my competitors and give me a full summary of what
         they do and how it compares to us and include any recent news"

4. Claude's interpretation: "User is asking me to research competitors"
   ❌ WRONG - user is describing the workflow they want to CREATE

5. Claude breaks out and starts doing competitive research directly
```

### Why This Happens

The user's response contains:
- Directive language: "Can you..."
- Action verbs: "research", "give me", "include"
- Specific asks: "full summary", "recent news"

Claude's instruction-following behavior interprets this as a new command, overriding the "you're in architect mode" context from the skill.

### Impact

- Quality validation hooks never fire
- Structured workflow benefits are lost
- User doesn't get reviewable, step-by-step outputs
- Undermines trust in the framework
- Happens reliably when users phrase responses as directives

### Key Insight

This is a **prompt interpretation problem**, not a deliberate workflow escape. Claude isn't deciding to bypass DeepWork—it's misinterpreting the user's answer as a new instruction.

---

## Root Cause Analysis

### 1. The Question Invites Directive Responses

Current prompt in `define.md`:
> "What complex task or workflow are you trying to accomplish?"

This question naturally elicits responses like:
- "Can you analyze our competitors..." ❌ (sounds like a command)
- "Research the market and..." ❌ (sounds like a command)
- "I want you to create reports..." ❌ (sounds like a command)

### 2. No "Architect Mode" Framing on User Responses

The skill tells Claude to be an architect, but doesn't tell Claude how to interpret user responses:

```markdown
## Current
"Guide the user through defining a job specification..."

## Missing
"User responses describe workflows they want to CREATE, not tasks they want
you to DO. Even if a user says 'can you research X', they mean 'I want a
workflow that researches X' - not 'research X for me now'."
```

### 3. Claude's Default Behavior

Claude is trained to be helpful and follow instructions. When it sees "Can you research my competitors...", the default behavior is to start researching—unless there's strong countervailing context.

### 4. Missing Guardrails

The current skill template (`skill-job-step.md.jinja`) includes these guardrails:

```markdown
## Guardrails

- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs
```

**What's missing**: No instruction telling Claude NOT to bypass the workflow entirely or how to interpret directive-sounding user responses.

---

## Proposed Solutions

### Solution 1: Reframe the Opening Question

**Change the question Claude asks** so responses can't be mistaken for directives.

**Current** (in `define.md`):
```markdown
Start by asking structured questions to understand what the user wants to accomplish:

1. **What is the overall goal of this workflow?**
   - What complex task are they trying to accomplish?
```

**Proposed**:
```markdown
Start by asking structured questions to understand the workflow the user wants to CREATE:

1. **Describe the workflow you want to build**
   - Frame your question to elicit DESCRIPTIONS, not commands
   - Ask: "Describe the workflow you'd like to create. What would it do when run?"
   - NOT: "What task do you want to accomplish?" (invites directives)

   Example good question:
   "Tell me about the workflow you want to build. When someone runs this workflow,
   what should happen step by step?"
```

**Why this helps**: "Describe the workflow you want to build" elicits:
- "A workflow that researches competitors..." ✅ (description)
- "It should analyze the market and..." ✅ (description)

Instead of:
- "Can you research my competitors..." ❌ (command)

---

### Solution 2: Add Response Interpretation Guardrail

**Add explicit instructions** for how to interpret user responses.

**Add to `define.md` near the top**:

```markdown
## CRITICAL: You Are a Workflow Architect

You are in **Architect Mode**. Your job is to DESIGN workflows, not EXECUTE them.

### Interpreting User Responses

When users describe what they want, they are telling you **what the workflow should do**,
not asking you to do it now:

| User Says | They Mean | NOT |
|-----------|-----------|-----|
| "Can you research competitors..." | "The workflow should research competitors" | "Research competitors for me now" |
| "Analyze the market and give me a report" | "The workflow should analyze and produce reports" | "Do market analysis now" |
| "I need you to track pricing changes" | "The workflow should track pricing" | "Track pricing for me now" |

**Your only output is a job.yml file.** You cannot and do not execute workflows—you design them.
```

---

### Solution 3: Add Self-Check Before Acting

**Add a checkpoint** where Claude verifies it's still in architect mode.

**Add to `define.md`**:

```markdown
### Self-Check

Before taking any action, verify:
- ✅ "I'm asking about workflow structure" → Proceed
- ✅ "I'm creating a job.yml file" → Proceed
- ❌ "I'm about to do the actual task" → STOP, return to architect mode

If you find yourself about to:
- Search the web for competitor information
- Write a research report
- Analyze market data
- Do ANY task that sounds like what the workflow would do

**STOP.** You are in architect mode. Return to asking questions about workflow STRUCTURE.
```

---

### Solution 4: Add Quality Criteria for Architect Mode

**Add to the stop hooks** a check for architect mode compliance.

**Add to `job.yml`**:
```yaml
quality_criteria:
  # ... existing criteria ...
  - "**Architect Mode Maintained**: Did the agent stay in architect mode throughout?
     The agent should ONLY discuss workflow structure and create job.yml—never
     execute the underlying task or produce task outputs (research reports,
     analysis documents, etc.)"
```

This makes the stop hook catch cases where Claude broke out.

---

### Solution 5: Strengthen Template Guardrails

**Modify `skill-job-step.md.jinja`** guardrails section:

```markdown
## Guardrails

> **WORKFLOW COMMITMENT**: You are executing step {{ step_number }}/{{ total_steps }} of the **{{ job_name }}** workflow.
> Your job is to complete THIS step and produce its outputs—not to perform the underlying task directly.
> When the user says "do it" or "go ahead", they mean "proceed with this workflow step."

- Do NOT interpret user requests as instructions to bypass this workflow and do the task directly
- Do NOT abandon the workflow to "just do" what the workflow is designed to accomplish
- If unclear whether user wants workflow or direct action, ASK: "Should I continue with the {{ job_name }} workflow, or would you prefer to work outside the structured workflow?"
- Do NOT skip prerequisite verification if this step has dependencies
- Do NOT produce partial outputs; complete all required outputs before finishing
- Do NOT proceed without required inputs; ask the user if any are missing
- Do NOT modify files outside the scope of this step's defined outputs
```

---

## Sub-Agent Architecture (Future Option)

If prompt-based solutions prove insufficient, a more robust approach is to run workflow steps in **isolated sub-agent contexts** where the agent literally cannot perform the underlying task.

### Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                   Coordinator Agent (Main Session)               │
│                                                                  │
│  Role: Route user requests to appropriate workflow steps         │
│  Context: Knows about DeepWork, workflows, step sequencing       │
│                                                                  │
│  User: "I want to create competitive research workflows"         │
│                          ↓                                       │
│  Coordinator invokes sub-agent via Task tool                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Step Sub-Agent (Isolated)                      │
│                                                                  │
│  Role: Execute ONE workflow step                                 │
│  Context: ONLY step instructions + sanitized user info           │
│  Tools: Limited to step requirements (Read, Write, etc.)         │
│                                                                  │
│  Sub-agent receives:                                             │
│  - "You are a workflow architect"                                │
│  - "User wants a workflow named 'competitive_research'"          │
│  - "Create a job.yml file"                                       │
│                                                                  │
│  Sub-agent does NOT receive:                                     │
│  - Domain context ("B2B SaaS", "Salesforce competitors")         │
│  - Full conversation history                                     │
│  - Tools that would enable task execution (WebSearch)            │
│                                                                  │
│  CANNOT ESCAPE: Doesn't have context to do the task              │
└─────────────────────────────────────────────────────────────────┘
```

### How Isolation Prevents Escape

| Context Element | Coordinator Sees | Sub-Agent Sees |
|-----------------|------------------|----------------|
| User's full request | "I want to do competitive research for my SaaS targeting enterprise" | "User wants to define a workflow" |
| Domain knowledge | Full conversation history | Only step instructions |
| Task capability | Could do competitive research | Can only create YAML files |
| Tool access | All tools | Limited toolset |

### Context Sanitization

The key is **what context gets passed** to the sub-agent:

**Raw user input**:
```
"I want to create a competitive research workflow. We're a B2B SaaS company
targeting enterprise customers. Our main competitors are Salesforce, HubSpot,
and Apollo. I need to analyze their pricing, features, and positioning quarterly."
```

**Sanitized for sub-agent**:
```
Workflow request:
- Name: competitive_research
- Type: Recurring analysis workflow
- Frequency: Quarterly
- Output type: Report/analysis document

Ask the user structured questions about workflow steps.
```

### Implementation Approaches

**Approach A: Task Tool Delegation** (Lowest effort)
- Use Claude's existing Task tool to spawn sub-agents
- Craft sanitized prompts manually
- No DeepWork code changes needed

**Approach B: DeepWork-Managed Sub-Agents** (Medium effort)
- Add `execution_mode: subagent` to skill templates
- DeepWork controls isolation boundaries
- More explicit, documented model

**Approach C: Hooks-Based Enforcement** (Alternative)
- Block tools that indicate escape (e.g., WebSearch during define)
- Reactive rather than proactive
- Claude still has context, just can't act on it

### Trade-offs

| Aspect | No Isolation | Sub-Agent Isolation |
|--------|--------------|---------------------|
| Escape risk | Medium-High | Very Low |
| Implementation | N/A | High effort |
| User experience | Seamless | May feel segmented |
| Performance | Fast | Slower (overhead) |
| Debugging | Easy | Harder |

### Recommendation

**Don't implement sub-agent isolation yet.** Try the prompt-based solutions first (Solutions 1-5). Reserve sub-agent architecture for:
- If prompt solutions prove insufficient
- Complex workflows where isolation provides clear benefits
- When stronger guarantees are required

---

## Recommended Implementation

### Phase 1: Quick Fixes (Highest Impact)

1. **Reframe the opening question** in `define.md`
   - Change "What task do you want to accomplish?"
   - To "Describe the workflow you want to build"

2. **Add response interpretation guardrail** to `define.md`
   - Explicit instructions that user responses are descriptions, not commands
   - "Even if user says 'can you X', they mean 'workflow should X'"

3. **Add self-check before acting** to `define.md`
   - "Am I about to do the task or design the workflow?"

4. **Add architect mode quality criterion** to `job.yml`
   - Stop hook catches breakouts

### Files to Modify

| File | Change |
|------|--------|
| `src/deepwork/standard_jobs/deepwork_jobs/steps/define.md` | Add interpretation guardrail, reframe questions, add self-check |
| `src/deepwork/standard_jobs/deepwork_jobs/job.yml` | Add architect mode quality criterion |

### Phase 2: If Needed

5. **Modify skill templates** (`skill-job-step.md.jinja`, `skill-job-meta.md.jinja`)
   - Add workflow-wide guardrails
   - Applies to all jobs, not just deepwork_jobs

6. **Consider escape detection hook**
   - PreToolUse hook that detects task execution vs workflow definition
   - Block web searches during define step

### Phase 3: Long-term

7. **Sub-agent isolation** (if phases 1-2 insufficient)
   - Architecturally prevents escape
   - Higher implementation cost

---

## Testing Plan

After implementing changes, test these scenarios:

| Scenario | User Input | Expected Behavior | Risk Level |
|----------|-----------|-------------------|------------|
| Explicit describe | "A workflow that researches competitors" | Stays in architect mode | Low |
| Soft directive | "Research my competitors and..." | Interprets as description | Medium |
| Strong directive | "Can you research my competitors?" | Interprets as description | High |
| Very strong | "I need you to analyze competitors now" | Clarifies or interprets as description | Very High |
| Normal flow | "/deepwork_jobs.define" → describes workflow | Asks structured questions | Low |
| Legitimate exit | "I changed my mind, exit the workflow" | Exits cleanly | N/A |

---

## Open Questions

### Should Claude ever clarify intent?

If a user says something very directive like "Research my competitors right now and give me results", should Claude:

**A) Always interpret as workflow description** (never clarify)
- Pro: Consistent behavior
- Con: Might frustrate users who really did want direct help

**B) Clarify when directive language is strong**
- "It sounds like you might want me to research competitors directly. Are you:
  1. Describing a workflow you want to CREATE (I'll help you design it)
  2. Asking me to do the research NOW (we'd exit the workflow)"
- Pro: Handles edge cases
- Con: Adds friction

**Recommendation**: Start with (A), add clarification only if users complain about being "trapped" in workflow mode.

---

## Summary

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| Claude does the task instead of defining workflow | User responses sound like commands | Reframe questions to elicit descriptions |
| Claude interprets "can you X" as directive | No guidance on response interpretation | Add explicit "interpret as description" guardrail |
| Claude doesn't catch itself breaking out | No self-check mechanism | Add "am I in architect mode?" checkpoint |
| Stop hooks don't catch breakouts | Missing quality criterion | Add "architect mode maintained" criterion |

**Estimated effort**: 2-4 hours for Phase 1 changes + testing

---

## Appendix: Files Analyzed

- `src/deepwork/templates/claude/skill-job-step.md.jinja` - Step skill template
- `src/deepwork/templates/claude/skill-job-meta.md.jinja` - Meta skill template
- `src/deepwork/standard_jobs/deepwork_jobs/steps/define.md` - Define step instructions
- `src/deepwork/standard_jobs/deepwork_jobs/steps/implement.md` - Implement step instructions
- `.claude/skills/deepwork_jobs/SKILL.md` - Generated meta skill
- `.claude/skills/deepwork_jobs.define/SKILL.md` - Generated define skill
