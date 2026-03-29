We are going to redo how Deepwork Jobs are structured and function. Do NOT do anything to maintain backwards compatibility - we will have a migration step that we will put in place that is all the support for compat we need.

A lot of the goal of this is cleaning up the relationship between DeepWork Reviews and the inline reviews in jobs.yml; going forward, we rely entirely on the infrastructure of DeepWork Reviews, and have jobs.yml depend on it.

## New File Format
1. There will be a new file format for `job.yaml` that will contain Job's info in a new style. Contents:
	1. `name` - like today
	2. `summary` - Brief description of it for discovery purposes
	3. `step_arguments` - an array of objects that are the inputs and outputs passed between various steps. Each has the following elements
		1. `name` - name of the argument. This is what is used to reference these as inputs and outputs of steps
		2. `description` - string description of the thing
		3. `type` - what format does it take. Valid values are `string` or `file_path`
		4. `review` - Instructions for reviewing the file. Identical to what .deepreview review blocks look like, and should reuse the same code.
			1. Be sure the docs clarify that this is IN ADDITION TO any normal .deepreview review rules.
		5. `json_schema` - optional argument that is a JSON schema for the file. Can be either a URI or a relative path.
	4. `workflows` key where most of the content of the file lives. This is an object where each key is the name of a workflow, and the body is an object with the following structure:
		1. summary - summary of what the workflow does (same as job.yml now)
		2. agent - optional field that sets the agent to use for the workflow (like in job.yml now). Defaults to general purpose (like today)
		3. common_job_info_provided_to_all_steps_at_runtime - same behavior as with job.yml now, but scoped to the workflow
		4. steps: an array of steps in order. Each step is an object with the following fields:
			1. `name` - Name of the step
			2. One of the following keys whose values are different for each key. This is the meat of the logic
				1. `instructions` - value is a string, and is inline instructions for the step
				2. `sub_workflow` - another workflow to invoke. It takes two keys:
					1. `workflow_name` - name of the other workflow to invoke
					2. `workflow_job` - what job is it in. Optional, in which case it defaults to the same job as the current workflow
			3. `inputs` - inputs to the step. This is an object where all the keys are references to `step_arguments` by name, and their values are objects with the following keys:
				1. `required` - boolean for if it is a required input. Defaults to true
			4. `outputs` largely the same as how `inputs` are structured, but in addition to `required`, there is an optional `review` key. This is the exact same format (and should reuse the existing code) as the `review` key in `.deepreview` files.
			5. NOTE: each step when finishing will be required to furnish all the outputs it has defined, and it will always be provided the inputs it requested when it starts.
			6. `process_requirements` - This is an object where each key is a name of an attribute and the body is a description of it. Note that these should be statements, not questions. They represent things about the *process and work* done in the step, not the individual output files, that need to be reviewed. Anything about the outputs that needs to be reviewed should be defined in the `outputs` under review, or the `step_arguments`. This is optional.
		5. `post_workflow_instructions` - this is an optional string. It is instructions returned to the agent after the final step is successfully finished and the workflow is complete.

## Runtime Process
1. The `finished_step` mcp tool 
	1. argument changes:
		1. `work_summary` that is a summary of the work done in the step
			1. `notes` should go away and be replaced by this
		2. `outputs` need to be clarified to be filepaths for file-type outputs and regular strings for others 
			1. This should be a `type` in the schema as it will get reused in the `start_workflow` step as mentioned below
	2. Behavior
		1. When the agent says it is done with a step, we will do a `quality criteria` pass, but do it in a way based entirely on the DeepWork Reviews infrastructure.
			1. For each `review` defined on an output (either in the output section or in the step_arguments for that argument), we treat it as a review rule and generate all the dynamic rules
				1. These all should have `common_job_info_provided_to_all_steps_at_runtime` added to them as part of the review instructions.
			2. We then treat it like normal review firing except the list of changed files is not from the git diff, but instead from the `outputs` list passed into the `step_finished` call.
				1. This means things like the `strategy` should still work normally in the `review` block - i.e. `individual` on an array-type file output would have separate reviews for each file, and the `matches_together` would group them together.
				2. We should include inputs by reference always too (for files) and by value for strings.
			3. If there is a `process_requirements`, then we make one review for that with
				1. Instructions of "You need to review the description of the work done as summarized below against the following quality criteria. If you find issues, assume that the work description could be incorrect, so phrase your answers always as telling the agent to fix its work or the `work_summary`.
				2. Still should get all the inputs and outputs too
				3. Be sure the `work_summary` gets passed to it labeled with that name so that any resulting errors reference the right thing
			4. When we get the list of reviews, it should not be JUST the dynamic ones, but also include any .deepreview file-defined rules as well.
			5. We need to honor the normal "skip ones that have already passed" logic too.
		2. If there are any reviews to run per the output of the above, we need to return the blob of instructions to run back to the agent in the exact same format that the get_reviews tool normally does. But we need to also return a block of instructions with it that has relevenat content from the /review skill we define on how to run there. It needs to also have instructions at the end to the effect of:
			1. "For any failing reviews, if you believe the issue is invalid, then you can call `mark_review_as_passed` on it. Otherwise, you should act on any feedback from the review to fix the issues. Once done, call `finished_step` again to see if you will pass now."
			2. This will result in the agent running the reviews itself until passing.
	3. If there is a json_schema defined for any file argument, then `step_finished` should parse the output file with the schema and fail with any errors from that right away before doing any more detailed reviews.
2. `start_workflow` needs to take any `inputs` to the first step in as an argument called `inputs`. It should use the exact same format as the `outputs` in `step_finished`.
3. The step_instructions that both `start_workflow` and `step_finished` return should include the inputs that the step expects.
4. When `step_finished` has the whole workflow ending, return the `post_workflow_instructions` in the response.
5. If a step in one workflow is of the type "sub_workflow", then just auto-generate instructions for now that say "call `start_workflow` with blah, blah, blah".


## Notes on todo tasks
1. Make sure that there is a file called `job.yml.guidance.md` that has really explanatory explanations of all the effects of the things in the job.yml file.
2. Make sure the schema is extremely detailed as well with comments explaining impacts of things as much as possible.
3. Make sure we have some real multi-step integration tests that try things like having the same outputs in multiple steps, there being .deepreview files defining reviews on the same files, etc.
4. Migrate all existing `standard_jobs` into the new format.
5. Update the `repair` workflow for individual job.ymls to drop everything it knows right now and just have instructions to rewrite any job.yml files that are not parsing fully into this new format.
6. Update the .deepreview file that we put into all new job folders to understand the new job.yml format
7. Make sure the e2e integration test still makes sense with these changes.