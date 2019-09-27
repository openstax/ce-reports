from datetime import datetime, timezone

import dateutil.parser


def _prepare_transfer(transfer):
    _transfer = dict(transferred_at=transfer["created_at"])
    _transfer["from_pipeline"] = transfer["from_pipeline"].get("name")
    _transfer["to_pipeline"] = transfer["to_pipeline"].get("name")
    return _transfer


def days_of_issue_in_pipeline(zenhub_client, repo_id, issue_num):
    """Returns the number of days an issue has been in the current pipeline"""
    issue = zenhub_client.get_issue(repo_id=repo_id, issue_number=issue_num)
    issue_events = zenhub_client.get_issue_events(
        repo_id=repo_id,
        issue_number=issue_num)

    transfers = [_prepare_transfer(e) for e in issue_events if
                 e["type"] == "transferIssue"]

    transfers = sorted(transfers, key=lambda x: x['transferred_at'])

    last_transfer = transfers[-1]

    delta = datetime.now(tz=timezone.utc) - dateutil.parser.parse(
        last_transfer["transferred_at"])

    return delta.days
