# Content Engineering Reports

The following reports are contained within the repository.

* [Pull Request Report](./reports/list_open_prs.py)
* [Kanban Policy Report](./reports/zenhub_policies.py)

### Open Pull Request Report

A report that posts to the #content-engineering slack channel which displays the status of all pull requests for each member of the team. The output looks like the following:

```
Outstanding Pull Requests
@ripal submitted poet#89 Log stack trace on error in bundleTreesHandler, updated 0 days ago:
   - Pending reviews from: N/A
@ripal submitted poet#86 Add git history as dependency and include button, updated 0 days ago:
   - Pending reviews from: @therealmarv, @chrisk
@ripal submitted cnx-epub#176 Prefix page IDs with page_ when formatting, updated 1 day ago:
   - Pending reviews from: @phil
@therealmarv submitted poet#88 Fix 1348 ensure ids, updated 2 days ago:
   - Pending reviews from: N/A
pyup-bot submitted cnx-automation#744 Scheduled monthly dependency update for July, updated 6 days ago:
   - Pending reviews from: N/A
@chrisk submitted staxly#102 (feat) Start CORGI jobs when book repos are tagged, updated 7 days ago:
   - Pending reviews from: N/A
@phil submitted output-producer-service#361 Show missing files during checksum, updated 30 days ago:
   - Reviewed by: @ripal (APPROVED)
   - Pending reviews from: N/A
Draft Pull Requests
No draft Pull Requests
```

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
