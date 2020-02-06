import json
import os
import re
from datetime import datetime, timezone

import dateutil.parser
from bs4 import BeautifulSoup
from ghzh import GitHubClient, ZenHubClient
from jinja2 import Template

from common.config import Config

from common.zenhub import days_of_issue_in_pipeline

ZENHUB_API_TOKEN = os.environ["ZENHUB_API_TOKEN"]
GITHUB_API_TOKEN = os.environ["GITHUB_API_TOKEN"]
CONFIG_NAME = os.environ["CONFIG_NAME"]

HERE = os.path.abspath(os.path.dirname(__file__))

if __name__ == "__main__":
    # Create Clients
    zh = ZenHubClient(token=ZENHUB_API_TOKEN)
    gh = GitHubClient(token=GITHUB_API_TOKEN)

    # Load the config
    config_file = os.path.join(HERE, CONFIG_NAME)
    config = Config(config_file)

    # Map config values to relevant variables
    output_template = Template(config.output_template)
    owner = config.repository_owner
    repository = config.repository_name
    workspace_id = config.zenhub_workspace_id
    global_policies = config.zenhub_policies["global"]
    pipeline_policies = [policy for policy in config.zenhub_policies["pipeline_policies"]]
    pipeline_names = [policy["pipeline_name"] for policy in pipeline_policies]

    repo = gh.repository(owner=owner, repository=repository)
    board = zh.get_board(workspace_id, repo.id)

    pipelines = [pipeline for pipeline in board["pipelines"] if
                 pipeline["name"] in pipeline_names]

    for pipeline in pipelines:
        for pipeline_policy in pipeline_policies:
            if pipeline["name"] == pipeline_policy["pipeline_name"]:
                pipeline.update(pipeline_policy)

    problem_pipelines = []

    for pipeline in pipelines:
        pipeline["policy_violations"] = []
        pipeline["problem_issues"] = []

        # Check WIP limit
        if (len(pipeline["issues"]) >= int(pipeline["wip_limit"])) and int(
                pipeline["wip_limit"] > 0):
            pipeline["policy_violations"].append(":rotating_light: Pipeline is beyond WIP Limit!")

        for issue in pipeline["issues"]:
            issue["policy_violations"] = []

            # We need to use github to access specific data like the description
            gh_issue = gh.issue(owner, repository, issue["issue_number"])

            # Check for acceptance criteria b/c we roll like that 
            if "acceptance_criteria" in pipeline and pipeline["acceptance_criteria"] == "required":
                acceptance_regex = re.compile(r"Acceptance Criteria")
                exit_regex = re.compile(r"Exit Criteria")
                soup = BeautifulSoup(gh_issue.body_html, "html.parser")

                acceptance_header = soup.find("h2", text=acceptance_regex)
                exit_header = soup.find("h2", text=exit_regex)

                if acceptance_header or exit_header:
                    if exit_header:
                        issue["policy_violations"].append(
                            ":warning: Rename '## Exit Criteria' header to '## Acceptance Criteria'")
                    header = acceptance_header or exit_header

                    acceptance_items = header.find_next_siblings("ul")

                    if not acceptance_items:
                        issue["policy_violations"].append(":warning: Needs Acceptance Criteria")

                else:
                    issue["policy_violations"].append(":warning: Needs Acceptance Criteria")

            # Check if the issue has an estimate
            if "estimate" not in issue and pipeline["estimate"] == "required":
                issue["policy_violations"].append(":game_die: Needs Point Estimate.")
                pipeline["problem_issues"].append(issue)

            # Check if issue has been in the pipeline too long
            issue["age"] = days_of_issue_in_pipeline(zh, repo.id, issue["issue_number"])
            if (issue["age"] > int(pipeline["card_max_days_limit"])) and pipeline[
                "card_max_days_limit"] > 0:
                issue["policy_violations"].append(
                    f"Card is {issue['age']} days old. "
                    f"Exceeds {pipeline['card_max_days_limit']} day limit.")

            # Add additional info if it's a problem issue
            if issue["policy_violations"]:
                issue["title"] = gh_issue.title
                issue["url"] = gh_issue.html_url

        # If any issues exist or there are pipeline violations append
        if pipeline["policy_violations"] or pipeline["problem_issues"]:
            problem_pipelines.append(pipeline)

    output = output_template.render(pipelines=problem_pipelines)
    print(output)
