# Triage & Scope

## Objective

Define the scope and context of the production investigation. This step gathers essential information about the issue and prepares for detailed analysis in subsequent steps.

## Task

Ask structured questions to understand the issue and create a triage document that guides the investigation.

### Step 1: Gather Issue Details

Ask structured questions to collect:

1. **Issue Description**
   - What is the user-reported symptom or problem?
   - When was the issue first detected?
   - Is this a new issue or a regression?

2. **Affected Components**
   - Which services, applications, or systems are affected?
   - What is the scope of impact? (single user, subset, all users)
   - Are there related systems that might be involved?

3. **Time Range**
   - When did the issue start?
   - Is the issue ongoing or resolved?
   - What time range should we investigate? (default: last 1 hour)

4. **Expected vs Actual Behavior**
   - What should be happening?
   - What is actually happening?
   - Are there any error messages or codes?

### Step 2: Define Investigation Scope

Based on the answers, document:

1. **Key Questions to Answer**
   - What specific questions will this investigation address?
   - What are the likely hypotheses?

2. **Services/Components to Monitor**
   - List specific service names for log queries
   - List specific metric names or patterns for Prometheus
   - List specific alert names to check

3. **Investigation Time Range**
   - Start and end times in ISO 8601 format
   - Prometheus-compatible time range (e.g., "[1h]", "[24h]")
   - Loki-compatible time range (e.g., "1h", "24h")

### Step 3: Create Triage Document

Create `triage.md` with this structure:

```markdown
# Investigation Triage: [Issue Title]

## Issue Summary
[Brief description of the problem]

**Status**: [Ongoing/Resolved]
**First Detected**: [Timestamp]
**Impact Scope**: [Description]

## Investigation Scope

### Time Range
- **Start**: [ISO timestamp]
- **End**: [ISO timestamp]
- **Duration**: [Human-readable duration]
- **Prometheus Range**: [e.g., [1h]]
- **Loki Range**: [e.g., 1h]

### Affected Components
- Service 1: [Service name and description]
- Service 2: [Service name and description]
- ...

### Key Questions
1. [Question 1]
2. [Question 2]
3. ...

### Investigation Hypotheses
1. [Hypothesis 1]
2. [Hypothesis 2]
3. ...

## Expected vs Actual Behavior

**Expected**: [What should happen]

**Actual**: [What is happening]

**Symptoms**: [Observable symptoms, error messages, etc.]

## Next Steps
- Check Alertmanager for active alerts (alert_check step)
- Analyze Prometheus metrics (metrics_analysis step)
- Review Loki logs (log_investigation step)
```

## Quality Criteria

Before completing this step, verify:

1. **Complete Information**: All essential details are gathered from the user
2. **Clear Scope**: The investigation boundaries are well-defined
3. **Specific Components**: Service names and metrics are concrete, not generic
4. **Valid Time Ranges**: Time ranges are formatted correctly for both Prometheus and Loki
5. **Actionable Questions**: Key questions are specific and answerable
6. **Document Created**: `triage.md` file exists and is well-formatted

## Output

- `triage.md` - Structured triage document ready for use by subsequent investigation steps
