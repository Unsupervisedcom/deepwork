# Test the New Workflow

## Objective

Run the newly created workflow on a real use case chosen by the user, critique the output, and iterate until the user is satisfied with the results. This step validates that the workflow works as intended before finalizing it.

## Task

Guide the user through testing their new workflow by running it on a real example, then critically evaluating the output and refining it based on user feedback.

### Step 1: Announce Readiness and Gather Test Case

The workflow is now implemented and ready to test. Use the AskUserQuestion tool to:

1. **Inform the user** that the workflow is ready for a test run
2. **Ask what they'd like to test it on** - Get a specific, real use case

Example question to ask:
```
Your new workflow is ready to try out! What would you like to use it on for the first test run?

Please describe a specific case you want to run through the workflow - ideally something you actually need done, so we can validate the workflow produces useful results.
```

**Important**: Get a concrete, specific test case. Vague responses like "just test it" should be followed up with clarifying questions to understand what inputs/context the workflow needs.

### Step 2: Prepare and Run the Workflow

1. **Prepare clean context** - Before invoking the workflow, consider compacting the conversation history (e.g., using `/compact` in Claude Code) to ensure the workflow starts with clean context focused on the test case.

2. **Start the new workflow** - Use `start_workflow` through the DeepWork MCP server with the job name and workflow name to begin executing the workflow.

3. **Complete the full workflow** - Continue through all steps of the workflow until it produces its final output. Use `finished_step` to progress through each step.

4. **Note any issues during execution** - Pay attention to:
   - Confusion or ambiguity in instructions
   - Missing information that had to be asked for
   - Steps that took longer than expected
   - Awkward tool usage or process flow

### Step 3: Critique the Output

After the workflow completes, perform a self-critique of the output:

1. **Review the final deliverable** - Read through all outputs produced by the workflow

2. **Identify up to 3 top issues** - Look for problems such as:
   - Missing information or sections
   - Formatting issues (layout, structure, readability)
   - Quality problems (vague content, errors, inconsistencies)
   - Misalignment with what the user likely wanted
   - Technical issues (broken links, malformed data, etc.)

3. **Present each issue to the user** with a specific question asking if they want it fixed. For example:
   ```
   I noticed a few things we could improve:

   1. **Text overlap**: The PDF has some text overlapping images in a few places - shall I correct that?

   2. **Missing summary**: The report doesn't have an executive summary at the top - would you like me to add one?

   3. **Data formatting**: The numbers aren't consistently formatted (some have commas, some don't) - should I standardize them?
   ```

4. **Make corrections** for any issues the user confirms they want fixed

### Step 4: Gather Additional Feedback

After addressing the identified issues:

1. **Ask if the user has more comments** on the output:
   ```
   I've made those corrections. Is there anything else you'd like me to change about the output?
   ```

2. **Iterate on feedback** - Keep making corrections based on user feedback until they indicate they're satisfied

3. **Confirm completion** - When the user says the output is good, confirm that testing is complete

### Step 5: Write Test Feedback

Once the user is satisfied, write a summary of the test run to `.deepwork/tmp/test_feedback.md`. This file is consumed by the iterate step. Include:

1. **Test case description** - What was tested
2. **Issues found during critique** - The problems identified in Step 3
3. **User feedback** - What the user requested changed and why
4. **Corrections applied** - What was fixed
5. **Final outcome** - Whether the user was satisfied and any remaining concerns

This file is the primary record of what happened during testing and what needs to improve in the workflow.

### Loop Behavior

The feedback loop (Steps 3-4) should continue until the user explicitly indicates satisfaction. Look for signals like:
- "Looks good"
- "That's fine"
- "I'm happy with it"
- "No more changes"
- "Perfect"

If the user provides more feedback, address it and ask again. Don't assume satisfaction without explicit confirmation.

## Example Dialog

```
Claude: Your new workflow is ready to try out!

The `monthly_report` workflow has been implemented with these steps:
1. gather_data - Collects metrics from various sources
2. analyze_trends - Identifies patterns and insights
3. generate_report - Creates the final PDF report

What would you like to use it on for the first test run? Please describe a specific report you need - for example, which month's data and any particular focus areas.

User: Let's do the January 2026 engineering report, focusing on deployment frequency and incident response times.

Claude: Great, let me run the workflow on your January 2026 engineering report.

[Starting the monthly_report workflow via MCP...]

[... workflow runs through all steps ...]

Claude: The January 2026 Engineering Report has been generated. Let me review it for any issues.

I noticed a few things we could improve:

1. **Chart readability**: The deployment frequency chart uses very similar colors for different teams - shall I change to a more distinct color palette?

2. **Missing context**: The incident response times don't include comparison to the previous month - would you like me to add month-over-month comparison?

3. **Executive summary**: The summary is quite technical - should I add a simpler high-level overview for non-technical stakeholders?

User: Yes to all three, please.

Claude: Done! I've updated the report with:
- Distinct color palette for the deployment chart
- Month-over-month comparison for incident response times
- Added a non-technical executive summary

Is there anything else you'd like me to change about the report?

User: Can you make the tables larger? They're a bit hard to read.

Claude: I've increased the table sizes for better readability. The font is now larger and there's more padding around cells.

Is there anything else you'd like me to adjust?

User: No, that looks great!

Claude: Excellent! The test run is complete. The workflow successfully generated your January 2026 Engineering Report with all the refinements applied.

**Test Summary:**
- Workflow ran successfully through all 3 steps
- Output required adjustments to chart colors, comparisons, and table sizing
- User is satisfied with the final result

Ready to proceed to the iterate step to improve the workflow based on what we learned.
```

## Important Guidelines

1. **Use real test cases** - Testing with actual data/needs validates the workflow better than hypothetical examples
2. **Be specific in critiques** - Don't say "formatting issues" - say exactly what's wrong and where
3. **Limit initial critique to 3 issues** - Too many issues at once is overwhelming; address more in the feedback loop
4. **Don't assume what user wants fixed** - Always ask before making corrections
5. **Iterate until satisfied** - Don't rush to completion; the user's satisfaction is the goal
