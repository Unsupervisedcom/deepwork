# Task Tool Flows

An experiment walking through the full lifecycle of Claude Code's Task tools, with all optional fields populated and blocking relationships.

## Step 1: Create 3 tasks (parallel)

**Call 1:**
```
TaskCreate({
  subject: "Set up database schema",
  description: "Create the initial PostgreSQL schema with users, posts, and comments tables. Include indexes and foreign keys.",
  activeForm: "Setting up database schema",
  metadata: { priority: "high", area: "backend", estimate: "30min" }
})
```
**Response:** `Task #1 created successfully: Set up database schema`

**Call 2:**
```
TaskCreate({
  subject: "Build API endpoints",
  description: "Implement REST endpoints for CRUD operations on users, posts, and comments. Depends on the database schema being ready.",
  activeForm: "Building API endpoints",
  metadata: { priority: "high", area: "backend", estimate: "45min" }
})
```
**Response:** `Task #2 created successfully: Build API endpoints`

**Call 3:**
```
TaskCreate({
  subject: "Write integration tests",
  description: "Write integration tests covering all API endpoints against a real test database. Depends on both schema and API being done.",
  activeForm: "Writing integration tests",
  metadata: { priority: "medium", area: "testing", estimate: "30min" }
})
```
**Response:** `Task #3 created successfully: Write integration tests`

---

## Step 2: Set up blocking relationships (parallel)

**Call 1:**
```
TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })
```
**Response:** `Updated task #2 blockedBy`

**Call 2:**
```
TaskUpdate({ taskId: "3", addBlockedBy: ["1", "2"] })
```
**Response:** `Updated task #3 blockedBy`

---

## Step 3: List all tasks

**Call:**
```
TaskList({})
```
**Response:**
```
#1 [pending] Set up database schema
#2 [pending] Build API endpoints [blocked by #1]
#3 [pending] Write integration tests [blocked by #1, #2]
```

---

## Step 4: Get full details on Task 1

**Call:**
```
TaskGet({ taskId: "1" })
```
**Response:**
```
Task #1: Set up database schema
Status: pending
Description: Create the initial PostgreSQL schema with users, posts, and comments tables. Include indexes and foreign keys.
Blocks: #2, #3
```

---

## Step 5: Start Task 1

**Call:**
```
TaskUpdate({ taskId: "1", status: "in_progress" })
```
**Response:** `Updated task #1 status`

*(At this point the spinner would show "Setting up database schema" -- that's the `activeForm` field in action.)*

---

## Step 6: Complete Task 1

**Call:**
```
TaskUpdate({ taskId: "1", status: "completed" })
```
**Response:** `Updated task #1 status`

---

## Step 7: Check board after completing Task 1

**Call:**
```
TaskList({})
```
**Response:**
```
#1 [completed] Set up database schema
#2 [pending] Build API endpoints
#3 [pending] Write integration tests [blocked by #2]
```

Task 2 is now unblocked (was `[blocked by #1]`, now free). Task 3 still shows `[blocked by #2]` -- the `#1` dependency was auto-resolved since it's completed.

---

## Step 8: Start and complete Task 2

**Call 1:**
```
TaskUpdate({ taskId: "2", status: "in_progress" })
```
**Response:** `Updated task #2 status`

**Call 2:**
```
TaskUpdate({ taskId: "2", status: "completed" })
```
**Response:** `Updated task #2 status`

---

## Step 9: Board after Task 2 done

```
#1 [completed] Set up database schema
#2 [completed] Build API endpoints
#3 [pending] Write integration tests
```

Task 3 is fully unblocked now.

---

## Step 10: Complete Task 3

**Call 1:**
```
TaskUpdate({ taskId: "3", status: "in_progress" })
```
**Response:** `Updated task #3 status`

**Call 2:**
```
TaskUpdate({ taskId: "3", status: "completed" })
```
**Response:** `Updated task #3 status`

---

## Final state

```
#1 [completed] Set up database schema
#2 [completed] Build API endpoints
#3 [completed] Write integration tests
```

---

## Key observations

1. **Responses are terse** -- `TaskCreate` returns a one-liner confirmation, `TaskUpdate` just says which field changed, `TaskList` is a compact summary.
2. **Blocking auto-resolves** -- When Task 1 completed, it disappeared from Task 2's `blockedBy` list automatically. Same for Task 2 -> Task 3.
3. **`TaskGet` is the detailed view** -- it showed the `Blocks: #2, #3` reverse-dependency info that `TaskList` doesn't include.
4. **`metadata` is fire-and-forget** -- I set `priority`, `area`, and `estimate` on all three tasks, but none of the list/get responses surfaced it back. It's stored but not displayed in the default views.
5. **`activeForm`** controls what the user sees in the spinner during `in_progress` -- it never appears in tool responses, only in the UI.
