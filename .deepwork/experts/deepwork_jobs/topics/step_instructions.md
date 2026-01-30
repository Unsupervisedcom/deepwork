---
name: Writing Step Instructions
keywords:
  - instructions
  - steps
  - markdown
  - writing
  - best practices
last_updated: 2025-01-30
---

# Writing Step Instructions

Best practices for writing effective step instruction files.

## File Location

Step instructions live in `.deepwork/jobs/[job_name]/steps/[step_id].md`.

The path is specified in job.yml via `instructions_file`:
```yaml
steps:
  - id: identify_competitors
    instructions_file: steps/identify_competitors.md
```

## Recommended Structure

### 1. Objective Section

Start with a clear objective statement:

```markdown
## Objective

Create a comprehensive list of competitors in the target market by
systematically researching industry players and their offerings.
```

### 2. Task Section

Detailed step-by-step process:

```markdown
## Task

### Step 1: Understand the Market

Ask structured questions to gather context:
- What industry or market segment?
- What product category?
- Geographic scope?

### Step 2: Research Sources

Search for competitors using:
1. Industry databases and reports
2. Google searches for market leaders
3. Customer review sites
...
```

### 3. Input Handling

If the step has user inputs, explicitly request them:

```markdown
## Inputs

Before proceeding, gather the following from the user:
- **market_segment**: Target market for analysis
- **product_category**: Specific product/service category

Use the AskUserQuestion tool to collect these inputs.
```

### 4. Output Format

Show what good output looks like:

```markdown
## Output Format

Create `competitors_list.md` with the following structure:

```markdown
# Competitors List

## Market: [market_segment]

### Competitor 1: Acme Corp
- **Website**: acme.com
- **Description**: Brief overview
- **Key Products**: Product A, Product B
```

### 5. Quality Criteria

Define how to verify the step is complete:

```markdown
## Quality Criteria

- At least 5 competitors identified
- Each competitor has description and key products
- Sources are cited for all information
- List is relevant to the specified market
```

## Key Phrases

### "Ask structured questions"

When gathering user input, always use this phrase:

```markdown
Ask structured questions to understand the user's requirements:
1. What is your target market?
2. Who are your main competitors?
```

This phrase triggers the AskUserQuestion tool which provides a better
user experience with clear options.

### "Use the Skill tool to invoke"

For workflow continuation:

```markdown
## On Completion

1. Verify outputs are created
2. Use the Skill tool to invoke `/job_name.next_step`
```

## Supplementary Files

Place additional reference materials in `steps/`:

```
steps/
├── identify_competitors.md
├── research_competitors.md
└── competitor_template.md    # supplementary reference
```

Reference them using full paths:
```markdown
Use the template in `.deepwork/jobs/competitive_research/steps/competitor_template.md`
to structure each competitor profile.
```

## Anti-Patterns to Avoid

### Vague Instructions
Bad: "Research the competitors"
Good: "Search each competitor's website, LinkedIn, and review sites to gather..."

### Missing Outputs
Bad: "Create a report"
Good: "Create `research_notes.md` with sections for each competitor..."

### Skipping Inputs
Bad: Assume inputs are available
Good: "Read `competitors_list.md` from the previous step. If it doesn't exist..."

### Generic Quality Criteria
Bad: "Output should be good quality"
Good: "Each competitor profile includes at least 3 data points with sources"

## Instruction Length

- Keep instructions focused and actionable
- Aim for 1-3 pages of content
- Extract lengthy examples into separate template files
- Use bullet points over paragraphs where appropriate

## Variables in Instructions

Instructions can reference job-level context. The generated skill includes:
- Job name and description
- Step position in workflow
- Dependencies and next steps
- All inputs and outputs

You don't need to repeat this metadata in instructions - it's included
automatically in the generated skill.
