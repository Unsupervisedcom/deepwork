# DeepPlan

DeepPlan is a feature of DeepWork that essentially creates a transient DeepWork Job Workflow meant for use a single time. It is helpful for coding activities, but CRITICAL for use for non-code activities that are non-trivial.

Mechanically, DeepPlan works as follows:
1. Agent is reminded via system prompt to always invoke the DeepWork Workflow of "create_deep_plan" every time it enters planning mode and starts work on a plan.
2. That workflows first instructions inform it the agent that the workflow is generally follow the pattern of instruction it was given for planning in general, but that the instructions from the workflow tools should supercede those planning instructions as they will lead to a better result.
3. The workflow is:
	1. Initial Understanding - Explore and understand what exists and clarify with the user. This also explicitly includes finding any documentation files that seem relevant to the request
		1. Outputs: 
			1. When you finish this step, include a FULL description of the user's request (not the findings of your investigations, just an explicit explanation of the user's request) in required Output called `original_user_request`. This MUST have the following format:
				1. ```
				   # User's Request (Verbatims)
				   ## Original Request
				   <verbatim of the original request>
				   ## Discussion
				   <All the messages that were actually exchanges with the user, NOT all status messages the Agent sent>
				   Agent: Question
				   User: Answer or extra statement
				   ```
			2. key_reference_files (array of filepaths) - Optional
			3. No reviews
			4. All the outputs of this should be inputs in ALL later steps.
		2. Be sure to clarify anything unclear during this process. Use AskUserQuestion for anything unclear
	2. Design Alternatives - Invoke additional agents to make competing designs for how to achieve the user's desired outcome
		1. As the agent's return their ideas, review each for if it achieves the user's request. If it fails to in some way, tell the agent of the issue and ask it to resolve the gap.
		2. If there are questions that arise from the plans, then use AskUserQuestion to clarify with the user.
		3. Unless told otherwise by the user explicitly or if the functionality is relatively trivial, there should be an Explore agent run that tries to identify if there are any existing open-source libraries that would provide substantial amounts of the functionality needed. If there are, then there should be a planning agent kicked off building a plan that uses those libraries as part of the plan.
		4. Outputs: None. No reviews either.
	3. Review and Synthesize
		1. Write the draft plan document. DO NOT call the exit planning tool.
		2. For any new libraries or dependencies being included in the plan, start an Explore agent searching the web for the latest versions of the libraries and seeing if there are any reason that the latest ones can't be used. The plan should include the specific versions of these libraries that are going to be used.
		3. Outputs:
			1. `draft_plan_file` - The draft plan
				1. Review: Does this plan achieve the `original_user_request`? Is anything missing?
			2. `key_affected_files` - full paths of the key files affected
	4. Enrich the Plan
		1. Your goal will be to make an enriched version of the plan that is structured as a DeepWork job definition.
		2. You must break the plan into multiple steps, where each step has validation steps to make sure the output is good.
		3. If there is work that would be appropriate for parallelization, then define separate workflows for those streams and have the main workflow have a step that instructs starting separate agents instructed to run those flows.
		4. The final step of the process must be `verify_completes_request` where all it does is review that the `original_user_request` has been satisfied, or to write a compelling summary of why the implementation was done differently than the original request. If there are gaps here, it can fix them at this stage
		5. A new MCP method - `register_session_job` - must be called to register the plan. It must error if there are any issues in the plan syntactically. Once done, this step can finish. This should take a name and the content of a job.yaml definition. This method can be called multiple times, over-writing the job definition.
			1. Note: I would strongly suggest that this be implemented as actually writing a job file in a tmp location so that there is a file that can be reviewed using the normal mechanisms. NOte that we can't have the agent write the file directly because plan mode disables file writing for anything but the plan file.
		6. Outputs:
			1. `session_job_name` - the name of the registered plan. There must be another MCP method - `get_session_job` - that retreives the definition. There must be a review of this that fetches the plan and reviews it for quality
				1. This also needs to be reviewed (separately) for whether it faithfully completes the `original_user_request`.
				2. Also needs
			2. `draft_plan_file` - reviewed to make sure it aligns with what is in the session_job.
	5. Present plan
		1. The plan should be amended to include a last line specifying that the plan will be executed using DeepWork with the job <the session job name>.
		2. The plan should then be presented to the user. 
		3. If the user asks for any changes, then the agent should go_to_step `enrich the plan`.
		4. Note: I think that if the plan is approved, the session is often cleared. That may mean that we need to also have the isntructions in the last line of the plan also say to end the planning deepwork workflow before starting the new one, since that line of isntructions is what will likely make the post-session-clearing process run deepwork properly.
