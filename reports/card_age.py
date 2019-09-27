import os

from ghzh import GitHubClient, ZenHubClient
from jinja2 import Template

from common.config import Config
from common.zenhub import days_of_issue_in_pipeline


ZENHUB_API_TOKEN = os.environ['ZENHUB_API_TOKEN']
GITHUB_API_TOKEN = os.environ['GITHUB_API_TOKEN']

HERE = os.path.abspath(os.path.dirname(__file__))


def _prepare_transfer(transfer):
    _transfer = dict(transferred_at=transfer["created_at"])
    _transfer["from_pipeline"] = transfer["from_pipeline"].get("name")
    _transfer["to_pipeline"] = transfer["to_pipeline"].get("name")
    return _transfer


if __name__ == "__main__":

    zh = ZenHubClient(token=ZENHUB_API_TOKEN)
    gh = GitHubClient(token=GITHUB_API_TOKEN)

    config_file = os.path.join(HERE, "card_age.yml")

    config = Config(config_file)

    output_template = Template(config.output_template)

    owner = config.repository_owner
    repository = config.repository_name

    repo = gh.repository(owner=owner, repository=repository)
    workspace_id = config.zenhub_workspace_id

    board = zh.get_board(workspace_id, repo.id)

    pipelines = [pipeline for pipeline in board["pipelines"] if
                 pipeline["name"] in config.zenhub_pipelines]

    suspect_issues = []

    for pipeline in pipelines:
        issue_numbers = [issue["issue_number"] for issue in pipeline["issues"] if
                         issue["is_epic"] is False]

        for issue_num in issue_numbers:

            days = days_of_issue_in_pipeline(zh, repo.id, issue_num)
            issue = zh.get_issue(repo_id=repo.id, issue_number=issue_num)

            if days > config.max_days_limit:
                gh_issue = gh.issue(owner, repository, issue_num)
                issue["age"] = days
                issue["issue_num"] = issue_num
                issue["title"] = gh_issue.title
                issue["url"] = gh_issue.html_url

                suspect_issues.append(issue)

    output = output_template.render(issues=suspect_issues)
    print(output)
