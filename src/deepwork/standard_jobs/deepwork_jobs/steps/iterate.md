# Iterate on Workflow Design

## Objective

Review the test run conversation and improve the job definition based on what happened. This step closes the feedback loop by incorporating learnings from the test into the workflow itself, making future runs more efficient and producing better results.

## Task

Analyze the conversation history from the test step, identify areas for improvement, and update the job definition and step instructions accordingly.

### Step 1: Review the Conversation History

Carefully analyze the conversation from the test step, looking for:

1. **Process Inefficiencies**
   - Steps that took multiple attempts to complete
   - Questions the agent had to ask that should have been in the instructions
   - Unnecessary back-and-forth with the user
   - Information that had to be repeated

2. **Output Quality Issues**
   - Issues identified during critique (from Step 3 of test)
   - Corrections requested by the user
   - Patterns in user feedback (what did they consistently want changed?)

3. **Tool Usage Problems**
   - Tools that didn't work as expected
   - Missing tools that would have helped
   - Inefficient tool sequences

4. **Missing or Unclear Instructions**
   - Ambiguities that led to wrong outputs
   - Missing guidance that caused confusion
   - Quality criteria that weren't clear enough

### Step 2: Plan Improvements

For each issue identified, determine the appropriate fix:

| Issue Type | Solution Location |
|------------|-------------------|
| Process inefficiency | Update step instructions with clearer guidance |
| Output quality | Update quality criteria or add examples |
| Missing information | Add to step inputs or instructions |
| Tool problems | Suggest different tools in instructions |
| Unclear criteria | Rewrite quality criteria to be specific |

**Prioritize improvements** that will have the most impact on future runs. Focus on:
- Issues that caused multiple iterations
- Problems that affected the final output quality
- Confusion that could be eliminated with clearer instructions

### Step 3: Update Step Instructions

For each step that needs improvement:

1. **Read the current instruction file** at `.deepwork/jobs/[job_name]/steps/[step_id].md`

2. **Make targeted improvements**:
   - Add missing context or clarification
   - Include examples of good output (use what worked in the test)
   - Clarify ambiguous instructions
   - Add tool recommendations if a different approach would be better
   - Update quality criteria to match user expectations

3. **Keep instructions concise**:
   - Avoid redundancy
   - Be direct and actionable
   - Use bullet points where appropriate

### Step 4: Update Quality Criteria

Review and update quality criteria in two places:

1. **In step instruction files** - The "Quality Criteria" section should reflect what the user actually cared about during testing

2. **In job.yml** - If steps have `quality_criteria` or `stop_hooks`, update them to:
   - Remove criteria that weren't relevant
   - Add criteria based on user feedback
   - Make existing criteria more specific

**Example improvement:**
```yaml
# Before
quality_criteria:
  - "Report is formatted correctly"

# After
quality_criteria:
  - "Report uses distinct colors for each data series in charts"
  - "Tables have sufficient padding and font size for readability"
  - "Executive summary is understandable by non-technical readers"
```

### Step 5: Consider Alternative Tools

If any tools didn't work well during the test:

1. **Identify the problem** - What went wrong? (slow, wrong output, hard to use)

2. **Research alternatives** - What other tools could accomplish the same goal?

3. **Update instructions** - If a better tool exists, update the step instructions to recommend it

Examples:
- If web scraping was unreliable, suggest a specific browser automation approach
- If data processing was slow, suggest a different method or tool
- If file generation had issues, recommend a different library or format

### Step 6: Update Job Version and Changelog

After making improvements:

1. **Bump the version** in `job.yml`:
   - Patch version (x.x.1) for minor instruction tweaks
   - Minor version (x.1.0) for quality criteria changes or significant improvements

2. **Add a changelog entry** describing what was improved:
   ```yaml
   changelog:
     - version: "1.0.1"
       changes: "Improved [step] instructions based on test run: added examples, clarified criteria, updated tool recommendations"
   ```

### Step 7: Provide Recap

Summarize the improvements made:

1. **List the issues identified** from the test run

2. **Describe the changes made** to address each issue

3. **Explain the expected impact** on future runs

Example recap format:
```
## Iteration Summary

### Issues Identified
1. Chart colors were hard to distinguish
2. Tables were too small to read
3. Executive summary was too technical

### Changes Made

**gather_data step:**
- Added instruction to use distinct color palettes for charts
- Updated quality criteria to require readable table formatting

**generate_report step:**
- Added example of good executive summary
- Updated quality criteria: "Summary understandable by non-technical stakeholders"

**job.yml:**
- Updated version to 1.0.1
- Added changelog entry

### Expected Impact
Future runs should produce reports with better visual design and clearer summaries, reducing the need for post-generation corrections.
```

## Quality Criteria

- Conversation history from test step was analyzed for issues
- Process inefficiencies were identified and addressed
- Step instructions were updated to improve clarity
- Quality criteria were updated to match user expectations
- Alternative tools were considered where relevant
- Job version and changelog were updated
- A clear recap of improvements was provided
- When all criteria are met, include `<promise>Quality Criteria Met</promise>` in your response

## Example Dialog

```
Claude: Let me review our test run and improve the workflow based on what happened.

**Analyzing Test Conversation...**

I identified the following issues from the test run:

### Issues Found

1. **Chart readability (gather_data step)**: The instructions didn't specify how to handle color choices for visualizations. During the test, we had to fix colors that were too similar.

2. **Missing month-over-month comparison (analyze_trends step)**: The user wanted comparisons to previous periods, but this wasn't in the instructions. We had to add it after the fact.

3. **Technical executive summary (generate_report step)**: The summary was too technical for non-technical stakeholders. The quality criteria didn't specify the audience clearly.

4. **Table formatting (generate_report step)**: Tables were hard to read. No guidance on sizing or padding.

### Changes Made

**`.deepwork/jobs/monthly_report/steps/gather_data.md`:**
- Added: "Use distinct, high-contrast colors for chart data series. Avoid similar shades for different categories."
- Added to Quality Criteria: "Charts use visually distinct colors that are accessible to colorblind readers"

**`.deepwork/jobs/monthly_report/steps/analyze_trends.md`:**
- Added: "Always include comparison to the same period in the previous month/quarter"
- Added input: "previous_period_data" to formalize this requirement

**`.deepwork/jobs/monthly_report/steps/generate_report.md`:**
- Added example of good executive summary targeting non-technical readers
- Added: "Format tables with sufficient padding (at least 8px) and readable font size (minimum 11pt)"
- Updated Quality Criteria:
  - "Executive summary is understandable by non-technical stakeholders"
  - "Tables are readable with adequate padding and font size"

**`.deepwork/jobs/monthly_report/job.yml`:**
- Version bumped to 1.0.1
- Added changelog: "Improved visual design guidance and audience-appropriate writing based on test feedback"

Running `deepwork sync`...

Done! The workflow has been updated.

### Expected Impact

Future monthly reports should:
- Have better chart color choices from the start
- Include month-over-month comparisons automatically
- Have clearer executive summaries for leadership
- Have more readable tables

This should significantly reduce the number of corrections needed after the initial output.
```

## Important Guidelines

1. **Be specific** - Don't just note "instructions were unclear" - explain exactly what was unclear and how you fixed it
2. **Use test results as examples** - If something worked well in the test, add it as an example in the instructions
3. **Don't over-engineer** - Only add improvements that address actual problems from the test
4. **Maintain consistency** - Keep the same structure and style in instruction files
5. **Test-driven improvement** - Every change should trace back to something that happened in the test
