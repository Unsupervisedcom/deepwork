When investigating consistency-reviewer issues, check these common root causes:

- **Outdated conventions**: The agent's core knowledge may describe a pattern that the codebase has since evolved away from. Check recent PRs to see if the convention changed.
- **Incomplete pattern knowledge**: The agent may know the general pattern but miss a valid variant. Check all existing examples of the pattern, not just the most common one.
- **Cross-domain confusion**: Job YAML conventions, step instruction conventions, and Python code conventions are related but distinct. An issue may stem from applying rules from the wrong domain.
- **Missing context about intent**: The agent reviews structural consistency but may lack context about why a particular deviation was chosen. Check PR descriptions and commit messages for rationale.
