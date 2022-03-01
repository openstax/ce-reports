# Content Engineering Reports

## How the reports work

The reports use a Concourse pipelines to execute. Concourse is our "continuous thing-doer." We are able to execute the reports in a series of steps as can be seen in in the following [example](https://github.com/openstax/ce-reports/blob/master/concourse/zenhub_policy_pipeline.yml#L2-L28):

```
---
resources:

  - name: daily-checkin
    type: time
    source:
      location: America/Chicago
      start: 10:30
      stop: 11:00
      days: [Monday, Tuesday, Wednesday, Thursday, Friday]

  - name: ce-reports
    type: git
    source:
      uri: https://github.com/openstax/ce-reports

jobs:
  - name: run-report
    build_log_retention:
      builds: 3
      minimum_succeeded_builds: 1
    public: true
    plan:
    - get: daily-checkin
      trigger: true
    - get: ce-reports
    - task: generate-report
      file: ce-reports/tasks/run-zenhub-policy-report.yml
```

The jobs typically run on a schedule using the `time` resource included with Concourse. The explanation of resources, jobs, and pipelines is out of scope for this document. If you wish to familiarize yourself with Concourse the [Stark and Wayne Tutorial](https://concoursetutorial.com/) is a great place to start.

Concourse pipelines have the capability to have tasks defined in file. If you review the last task in the examble above you can see we run the task included within the ce-reports repository in `./ce-reports/tasks/run-zenhub-policy-report.yml`

The following report is contained within the repository.

* [Kanban Policy Report](./reports/zenhub_policies.py)

### Kanban Policy Report

The kanban policy report was designed to codify kanban policies in a manner that is working code and documentation at the same time. The ideas powering Kanban are useful to understand to know why these policies are important.

Briefly, Kanban is a pull system to regulate the "flow" of work. Kanban is a Lean idea popularized in books like [_The Phoenix Project_](https://www.goodreads.com/book/show/17255186-the-phoenix-project) and originates in practices used at Toyota, which have been adapted to software engineering. Kanban makes software development work more visible and limits Work In Progress (WIP) to create a steady flow of work.

Each step in a process should exist as a separate column on a Kanban board and cards should only be pulled into the next step of the process. This is very different than the way a lot of other shops work who push things into the QA queue or the developer queue whenever the person thinks they are "done". Kanban policies are developed by the team and should be explicit to everyone. The policies dictate requirements like acceptance criteria, tests plans, or point estimates to be defined before cards can be pulled by someone to begin work.

The Kanban Policy Report uses a [yaml configuration](./reports/ce_zenhub_policies.config.yml) file that looks like this:

```
repository_name: cnx
repository_owner: openstax
zenhub_workspace_id: 5af1f4cc12da5e6d74331b60
zenhub_policies:
  global:
    pull_request_without_issue: create
  pipeline_policies:
    - pipeline_name: "Needs Decomp/Analysis"
      wip_limit: 0
      card_max_days_limit: 7
    - pipeline_name: "WIP: 4 - Coding/Development"
      wip_limit: 4
      card_max_days_limit: 7
      estimate: required
      acceptance_criteria: required
    - pipeline_name: "WIP: 3 - Needs Code Review"
      wip_limit: 3
      card_max_days_limit: 3
      estimate: required
      acceptance_criteria: required
```

This configuration file is read by a python script that communicates with GitHub and ZenHub to post to slack any violations that exist to any of our "codified" Kanban policies.

The following checks take place during the report that we've agreed should be policies:

* A check that Acceptance Criteria exists on the issue.
* Issues should only be in specific pipelines for a set amount of days. This is to signal to the team that we may need break up cards or things are more complicated than they initially seemed.
* An estimate should exist if it's to be added to ready to start. 
* WIP limits are not exceeded in the various pipelines.

## How to update the reports

If a change occurs in either of the reports at the task level there should be no need to make any changes to the pipeline. The pipeline should automatically detect changes to this repository, pull a copy, and execute the pipeline. If a change occurs in the pipeline definition itself this will require the exectution of the `fly` cli tool that interacts with Concourse to set the pipeline.

As an example, we'll update the kanban policy report. If the pipeline code changes the timer that the report will execute we'll need to update Concourse with the new pipeline.

### Login to Concourse with your LDAP username and set a target

> Note :pencil:: You can download the fly executable from the Concourse web address. The current address at the time of this writing is https://concourse-v6.openstax.org. From the main page download the executable to a place on your local machine. You may want to update your configuration to place fly in your PATH variable. You may need to alter the Concourse url if a new version has been deployed.

Run the following to login to concourse and set a target:

```
fly login --target v6 --concourse-url https://concourse-v6.openstax.org --team-name CE
```

You will be directed to visit a web address to login to Concourse. Upon successful login with LDAP credentials the fly command will prompt you that your target has been saved. Your token will be saved locally along with your target in your `~/.flyrc` file. At this point, you can continue to execute fly commands to update the pipeline.

### Update the report by using fly set-pipeline

To update the pipeline you'll first need to locate the pipeline file you'd like to update. These are located in the [./concourse](directory). In the following example we'll update the ZenHub Policy Report.

To update the report we run the set-pipeline command:

```
fly --target v6 set-pipeline --config ./concourse/zenhub_policy_pipeline.yml --pipeline report-kanban-policy
```

The fly CLI will prompt you to accept the changes by presenting a diff. Accept to approve the changes or cancel if you see any mistakes.

> FIXME :warning:: We've documented the process to update the kanban policy report but need more documentation on how to update the Open Pull Requests. It appears there is a vars file with some secrets. This documentation needs to be updated with that process.