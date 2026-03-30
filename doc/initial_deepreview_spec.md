# DeepSchema
DeepWork Schemas (or DeepSchemas) are an enrichment of the DeepReview system wherein you can have a rich schema for files that are helpful for both humans and for agents.

## Types of DeepSchemas
1. `named` DeepSchemas are ones placed in `.deepwork/schemas/` or a similar schema registry. 
2. `anonymous` DeepSchemas are ones that are declared in the normal file system alongside files they affect. These are specific to individual files, and have names of the format `.deepschema.<filename>` where `filename` is the file they apply to.

## Named DeepSchemas
Named DeepSchemas are directories where the final segment of the path is the name of the schema. The files inside the directories are then as follows:
* deepschema.yml - the manifest file
* `examples` - a directory of example files
* `references` - additional reference files relevant to the schema
* `schema file with any name` - JSON Schema for the file or any other types of normal schemas go in the main directory. All optional

## Anonymous DeepSchemas
These have only the single file. That file is the same format as the `deepschema.yml` file in the named DeepSchemas.

## Files
### deepschema.yml
These yaml files have the following keys. They are all usable in both anonymous and named DeepSchemas, but we separate them below into the ones that are common in both and ones mostly relevant to Named ones.
1. Common to Both
	1. `requirements` - object where the keys are names and the bodies are descriptions of the requirements that a good document meets. These use RFC 2119 words that guide the reviews; MUST, SHOULD, etc. This is the same format / type as `process_quality_attributes` in DeepWork Jobs which needs to be updated to be called `process_requirements`
	2. `parent_deep_schemas` - array of the names of other schemas that apply to anything this applies to.
		1. Mostly used in anonymous DeepSchemas to reference in a named DeepSchema when needed
	3. `json_schema_path` - relative path to a JSON schema file to enforce
	4. `verification_bash_command` - arbitrary array of strings of bash commands to be run on the file to verify it. Main example use is if there is a different kind of schema other than a JSON one that you want to enforce
2. `summary` Summary of the type. Used for giving a high-level understanding and for search / discovery
3. `instructions` - general instructions for dealing with files of this type. 
4. `examples` - array of examples of files of this type done well. Each entry should have a relative path from the definition file and a description.
5. `references` - more detailed reference files that can be looked at on particular topics related to the file. These have relative paths and descriptions. Can also also have URLs in place of relative paths
6. `matchers` - a declaration of file patterns that the schema applies to. This is an array of glob patterns

## Behavior
1. There must be a concept of "applicable schemas" for a given file. This should be computed using a reusable method. It should match any named schemas that have matchers that match up with a given file, or anonymous schemas named appropriately for that file
2. Whenever a file is read by an agent, there must be a message sent to the agent after the read that says "Note: this file must confirm to the DeepSchema at <project relative path/>"
3. Whenever a file is written by an agent, the `verification_bash_command` must be executed automatically. If it fails, then a message must be returned to the agent saying "CRITICAL: DeepSchema validation failed when it tried to verify this change. Error: <stdout + stderr from the failed command/>"
	1. If there was a `json_schema_path`, then it must also generate a similar message if the file does not conform to the schema
4. DeepReview must be modified so that there are "reviews" generated for every type definition. 
	1. These should have the relevant deepschema.yml used as the origin file.
	2. They should all be single-file-at-a-time reviews
	3. Their names should be "<named schema name | anonymous schemas target file name/> DeepSchema Compliance"
	4. The instructions for the review should be (roughly): 
		1. Named schemas intro: "<file path/> is an instance of <schema name/>, described as follows:\n<schema summary/>\n\nInstructions for dealing with these files:\n<instructions/>"
		2. Anonymous schemas intro: "<file path/> has requirements that it must follow."
		3. Body for both types: "Please review for compliance with the following requirements. You must fail reviews over anything that is MUST. You must fail reviews over any SHOULD that seems like it could be easily followed but is not. You should give feedback but not fail over anything else applicable. You can ignore N/A requirements.\n\n <requirements/>"
	5. These reviews should run both from `/review` and from DeepWork jobs when steps finish like regular DeepReviews are run
