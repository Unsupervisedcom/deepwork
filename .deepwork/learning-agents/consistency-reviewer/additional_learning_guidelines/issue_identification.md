When identifying issues for the consistency-reviewer agent, focus on:

- Cases where the agent missed an inconsistency that later caused a runtime failure or confusion
- Cases where the agent flagged something as inconsistent that was actually an intentional and valid deviation
- Cases where the agent's review missed data flow integrity issues between steps
- Cases where the agent applied conventions from one domain (e.g., Python code) to another domain (e.g., job YAML) inappropriately

Ignore:
- Minor formatting disagreements that didn't affect outcomes
- Cases where the PR author intentionally chose a different approach and documented why
