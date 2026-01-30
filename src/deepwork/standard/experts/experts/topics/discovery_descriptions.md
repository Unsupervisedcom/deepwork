---
name: Writing Discovery Descriptions
keywords:
  - discovery
  - description
  - routing
  - selection
last_updated: 2025-01-30
---

# Writing Effective Discovery Descriptions

The `discovery_description` determines when your expert gets invoked. It's the
"elevator pitch" that helps the system route queries to the right expert.

## Purpose

Discovery descriptions are used by other parts of the system to decide:
- Whether to suggest this expert for a task
- Which expert to invoke when multiple could apply
- How to present the expert to users

## Anatomy of a Good Description

```yaml
discovery_description: |
  Ruby on Rails ActiveJob - background job processing including
  queue configuration, retry strategies, error handling, and
  integration with queue backends like Sidekiq and SolidQueue.
```

Components:
1. **Domain identifier**: "Ruby on Rails ActiveJob"
2. **Core capability**: "background job processing"
3. **Specific coverage**: "queue configuration, retry strategies..."
4. **Boundaries**: "integration with queue backends like..."

## Guidelines

### Be Specific
Bad: "Helps with background jobs"
Good: "Rails ActiveJob background processing - queues, retries, error handling"

### Include Key Terms
Include terms users would search for. If someone asks about "Sidekiq retries",
the description should contain those words.

### Set Boundaries
Indicate what's in and out of scope. "...including X, Y, Z" signals coverage.

### Keep It Scannable
1-3 sentences max. The system needs to quickly evaluate relevance.

### Avoid Marketing Speak
Bad: "The ultimate guide to mastering background jobs"
Good: "ActiveJob configuration, error handling, and queue backend integration"

## Examples

### Too Vague
```yaml
discovery_description: Helps with Rails development
```

### Too Narrow
```yaml
discovery_description: How to configure exponential backoff in ActiveJob
```

### Just Right
```yaml
discovery_description: |
  Rails ActiveJob expertise - background job processing, queue
  configuration, retry strategies, error handling, and integration
  with Sidekiq, SolidQueue, and other queue backends.
```

## Testing Your Description

Ask yourself:
1. If I had this problem, would I find this expert?
2. Does it differentiate from similar experts?
3. Can I tell what's covered in 5 seconds?
