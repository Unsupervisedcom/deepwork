# Overview
DeepWork is framework for making AIs perform complex, multi-step work tasks. It is heavily inspired by the https://github.com/github/spec-kit project that provides such a framework for software development using a spec-driven approach. However, DeepWork is meant to work for a far-broader universe of task types.

# Key Concepts
DeepWork has 2 main concepts
## Jobs
Jobs are the complex, multi-step things we do all the time. In DeepWork, you define a Job once, then can have Agents do that job for you many times. For example, Feature Development, Ad Campaign Design, Competitive Research, Monthly Sales Reporting, Data-Driven Research, etc.

## Steps
Each job is made up of a series of steps. Steps are defined by having an input and an output that can be reviewed. For example, SpecKit has steps of `constitution` to define invariants for the development process, `specify` for writing the specification, `plan` for making a development plan off the specification, etc. Competitive Research might have steps of `identify_competitors`, `primary_research` (looking at what competitors say about themselves), `secondary_research` (what others say about the competitors), `report` that writes detailed reports on how the competitors (and yourself) compare, and `position` that defines a process for positioning against competitors.

Each of these become commands that can be invoked in Agent platforms like Claude Code to facilitate going through the process. For example, `/competitive_research.identify_competitors`

# Git
DeepWork is designed to be used with Git. The expectation is that you will make Git repositories for the work you do with the tool so that you can track and version both the job definitions and the products of the work. It also means that many of the key processes needed around agent-assisted work can be handled with Git integrations, such as Github Actions that fire when a PR merges.

# How it Works

## Install
Users install DeepWork on their local machine as a CLI. They then invoke it in a git project directory with the command `install --gemimi` or `install --claude` or similar where their tool of choice is declared.

That installs several commands in the project for the CLI you chose.

Everything after that is done using the CLI you chose. i.e. you use `/deepwork.define` that is mentioned below will be run in Claude Code as a slash-command in the project directory.

## Define Jobs

The main command installed above is now used for getting your jobs defined:
* deepwork.define - Works with the user to define a new Job with all of the Steps involved in it

The jobs that are defined this way are stored inside the project so that they get git-tracked alongside work product.

## Do Jobs
When you want to do a new job, you just start it with the appropriate command. This will trigger the creation of a Git branch for the new work and start going.

You will then need to go through the flow of the job between the various steps. Each step will have reviewable output files that you can look at and make sure are correct. Once you are happy with the output, you can go on to the next step.

We encourage you to commit the artifacts to git as you go. Once you have the final output in a great place, you can send your PR for review to other people on your team, and ultimately merge it.

## Learn
We need to refine our Job definitions as we work so that we keep getting better. 
You can  call `/deepwork.refine` that will let you update a given job based on new info.

Additionally, having all the work products in Git makes it easy for the Agents to have wide context. For example, if you are doing competitive research on a new competitor, the existing research on others acts as a template for both style and thinking for the agents.

