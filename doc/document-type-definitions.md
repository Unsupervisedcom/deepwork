# Document Type Definitions (DTDs)

Document Type Definitions (DTDs) are a first-class feature in DeepWork that formalize document specifications with quality criteria. They enable consistent document structure across job outputs and automated quality validation.

## Overview

DTDs solve a common problem: when AI agents produce documents (reports, summaries, analyses), the quality can be inconsistent. DTDs provide:

- **Consistent Structure**: Define the required sections and format once
- **Quality Criteria**: Specify measurable quality requirements
- **Example Documents**: Show what good output looks like
- **Reusability**: Use the same DTD across multiple jobs

## DTD File Format

DTD files use frontmatter markdown format and are stored in `.deepwork/dtds/[dtd_name].md`:

```markdown
---
name: "Monthly AWS Spending Report"
description: "A Markdown summary of AWS spend across accounts"
path_patterns:
  - "finance/aws-reports/*.md"
target_audience: "Finance team and Engineering leadership"
frequency: "Monthly, following AWS invoice arrival"
quality_criteria:
  - name: Visualization
    description: Must include Mermaid.js charts showing spend per service
  - name: Variance Analysis
    description: Must compare current month against previous with percentages
  - name: Action Items
    description: Must include specific cost optimization recommendations
---

# Monthly AWS Spending Report: [Month, Year]

## Executive Summary
[Example content showing expected structure...]

## Spend Overview
[Example content...]
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Human-readable document name |
| `description` | Yes | Brief description of the document's purpose |
| `quality_criteria` | Yes | Array of `{name, description}` objects defining quality requirements |
| `path_patterns` | No | Glob patterns for where documents should be stored |
| `target_audience` | No | Who the document is written for |
| `frequency` | No | How often the document is produced |

### Quality Criteria

Each quality criterion has:
- **name**: Short identifier (e.g., "Visualization", "Variance Analysis")
- **description**: Detailed explanation of what the criterion requires

Write criteria to be:
- Specific and measurable
- Actionable for the AI agent
- Verifiable upon completion

**Good example:**
```yaml
- name: Visualization
  description: Must include at least one Mermaid.js chart showing spend breakdown by service
```

**Poor example:**
```yaml
- name: Quality
  description: Should be good quality
```

### Example Document

The markdown body after the frontmatter serves as an example document. This shows:
- Expected section structure
- Placeholder content format
- Any required elements (tables, charts, etc.)

## Using DTDs in Jobs

### Referencing a DTD in job.yml

When a step produces a document that should follow a DTD, reference it in the outputs:

```yaml
steps:
  - id: generate_report
    name: "Generate Monthly Report"
    description: "Create the monthly AWS spending report"
    instructions_file: steps/generate_report.md
    outputs:
      - file: reports/aws_spending.md
        dtd: monthly_aws_report  # References .deepwork/dtds/monthly_aws_report.md
```

### What Happens During Sync

When you run `deepwork sync`:

1. The generator loads all DTDs from `.deepwork/dtds/`
2. For outputs with DTD references, the DTD information is included in the generated skill
3. The skill includes:
   - Document name and description
   - Target audience (if specified)
   - All quality criteria with descriptions
   - Example document structure (in a collapsible section)

### Generated Skill Output

The skill will include a section like:

```markdown
## Outputs

**Required outputs**:
- `reports/aws_spending.md`

  **Document Type**: Monthly AWS Spending Report
  > A Markdown summary of AWS spend across accounts

  **Target Audience**: Finance team and Engineering leadership

  **Quality Criteria**:
  1. **Visualization**: Must include Mermaid.js charts showing spend per service
  2. **Variance Analysis**: Must compare current month against previous with percentages
  3. **Action Items**: Must include specific cost optimization recommendations

  <details>
  <summary>Example Document Structure</summary>
  [Example markdown content...]
  </details>
```

## Creating DTDs

### Using /deepwork_jobs.define

When you run `/deepwork_jobs.define` to create a new job, the agent will:

1. Detect document-oriented workflows (keywords like "report", "summary", "monthly")
2. Offer to create a DTD for the document type
3. Ask structured questions about quality criteria, audience, and structure
4. Create the DTD file before proceeding with job definition

### Manual Creation

You can also create DTDs manually:

1. Create a new file in `.deepwork/dtds/[dtd_name].md`
2. Use lowercase with underscores for the filename (e.g., `monthly_aws_report.md`)
3. Follow the template in `.deepwork/jobs/deepwork_jobs/templates/dtd.md.template`

## Improving DTDs Over Time

### Using /deepwork_jobs.learn

When you run `/deepwork_jobs.learn` after executing a job with DTD outputs, the agent will:

1. Review the conversation for DTD-related learnings
2. Identify quality criteria that were unclear or insufficient
3. Note structural changes that were requested
4. Update the DTD file with improvements

### What to Look For

Signs that a DTD needs improvement:
- Repeated validation failures on specific criteria
- User requests for additional sections
- Confusion about what a criterion requires
- Changes to document format or structure

### Making Updates

When updating a DTD:

1. **Quality criteria**: Add, modify, or remove criteria based on learnings
2. **Example document**: Update structure to reflect changes
3. **Metadata**: Update audience, frequency, or path patterns if needed

## Best Practices

### Quality Criteria

1. **Be specific**: "Include spend comparison table with last 3 months" not "Include comparison"
2. **Be measurable**: Criteria should be verifiable
3. **Start with 3-5 criteria**: Add more as patterns emerge
4. **Use descriptive names**: Names should convey the criterion's purpose

### Example Documents

1. **Show structure, not content**: Use placeholders like `[Description here]`
2. **Include all required elements**: Tables, charts, sections
3. **Keep it concise**: Long enough to show structure, short enough to scan

### Organization

1. **One DTD per document type**: Don't combine different document types
2. **Use descriptive filenames**: `quarterly_review.md` not `report.md`
3. **Group related path patterns**: All storage locations for a document type

## Example: Complete Workflow

1. **Define job with DTD**:
   ```
   User: /deepwork_jobs.define
   Agent: What workflow would you like to create?
   User: I need to create monthly AWS spending reports for leadership
   Agent: I detect this is a document-oriented workflow. Let me help you define a DTD first...
   ```

2. **DTD is created** at `.deepwork/dtds/monthly_aws_report.md`

3. **Job references DTD** in final step output:
   ```yaml
   outputs:
     - file: reports/aws_$(date +%Y_%m).md
       dtd: monthly_aws_report
   ```

4. **Sync generates skill** with quality criteria included

5. **Execute job**: Agent produces document following DTD structure and criteria

6. **Learn and improve**:
   ```
   User: /deepwork_jobs.learn
   Agent: I found that the "Action Items" criterion was too vague.
          Updating to require "3 specific recommendations with estimated savings"
   ```

## Validation

DTD files are validated against a JSON schema when loaded. Required fields:
- `name`: Non-empty string
- `description`: Non-empty string
- `quality_criteria`: Array with at least one criterion, each having `name` and `description`

If validation fails during sync, you'll see an error message indicating what needs to be fixed.
