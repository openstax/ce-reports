#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from time import sleep
from urllib.request import Request, urlopen

GITHUB_BEARER_TOKEN = os.environ['GITHUB_BEARER_TOKEN']
GITHUB_ENDPOINT = 'https://api.github.com/graphql'
# The variables for the GraphQL pull
PULL_PAGE_SIZE = os.environ['PULL_PAGE_SIZE']
MAX_REPOSITORIES_PULLED = os.environ['MAX_REPOSITORIES_PULLED']
ORGANIZATIONS = os.environ['ORGANIZATIONS'].split(',')
MAX_PR_AGE = int(os.environ.get('MAX_PR_AGE', 31))
# DEVELOPERS should look like this:
#   {"karenc": ["<@U0F9C99ST>", "@karen"],
#    "pumazi": ["<@U0F988KSQ>", "@mulich"],
#    "therealmarv": ["<@U340WT25C>", "@therealmarv"],
#    "philschatz": ["<@U0F5LRG3Z>", "@phil"],
#    "m1yag1": ["<@U0F55RAAG>", "@mike"],
#    "brenguyen711": ["<@UKPA5MS1X>", "@brenda"],
#    "omehes": ["<@UDGTHPLQ6>", "@Ottó"]}
DEVELOPERS = json.loads(os.environ['DEVELOPERS'])
# REVIEWERS should look like this:
#   {"helenemccarron": ["<@U0FU55RRT>", "@hélène"],
#    "tomjw64": ["<@U199K9DTJ>", "@Thomas"],
#    "brittany-johnson": ["<@U7FHVAJ4T>", "@BrittanyJ"],
#    "scb6": ["<@U835RC4HH>", "@scott"]}
REVIEWERS = json.loads(os.environ['REVIEWERS'])
REVIEWERS.update(DEVELOPERS)
# BOTS should look like this:
#  {"pyup-bot": ["cnx-automation", "cnx-deploy", "cnx-press"]}
BOTS = json.loads(os.environ['BOTS'])


def query_github(query, org, states):
    i = 1
    nodes = []
    cursor = None
    # Query as much pages needed to reach the maximum repositories to pull
    while PULL_PAGE_SIZE * i <= MAX_REPOSITORIES_PULLED:
        i += 1
        # format the query to add if needed the current cursor
        formatted_query = query % (org, PULL_PAGE_SIZE, cursor if cursor else '', states)
        req = Request(GITHUB_ENDPOINT, method='POST', data=json.dumps({'query': formatted_query}).encode('utf-8'),
                      headers={'Authorization': 'bearer {}'.format(GITHUB_BEARER_TOKEN)})
        # Sometimes the Github endpoint returns inconsistent results or the calls fail, so we retry
        # The inconsistent 502 error should be solved by the pagination fix,
        content = http_call_with_retry(request=req, max_retries=3)
        if not content:
            sys.stderr.write('{}\n'.format(query))
            break
        data = content['data']['organization']['repositories']
        nodes.extend(data['nodes'])
        if data['pageInfo'] and data['pageInfo']['hasNextPage']:
            # Retrieving the current cursor for the next query.
            cursor = f' after: "{data["pageInfo"]["endCursor"]}" '
        else:
            break
    return nodes


def http_call_with_retry(request: Request = None, max_retries: int = 1):
    """This method is used to retry http calls in case they fail."""
    if request:
        retries = 1
        while retries <= max_retries:
            retries += 1
            try:
                content = json.loads(urlopen(request).read().decode('utf-8'))
                if 'errors' in content:
                    sys.stderr.write(f'HTTP call failed with url: {request.full_url}')
                    raise RequestCallFailedException(f'Error when querying {request.full_url}')
                else:
                    return content
            except Exception as e:
                sys.stderr.write(f'{e}')
                if retries < max_retries:
                    continue
                else:
                    break
            sleep(2)
    return None


def get_open_prs(org, states):
    query = """\
query {
    organization(login: "%s") {
        repositories(orderBy: { field: UPDATED_AT, direction: DESC }
                     first: %s %s ) {
            nodes {
                name
                pullRequests(states: %s
                             first: 20
                             orderBy: { field: UPDATED_AT, direction: DESC }) {
                    nodes {
                        url
                        title
                        number
                        isDraft
                        createdAt
                        updatedAt
                        author {
                            login
                        }
                        commits(last: 1) {
                            nodes {
                                commit {
                                    pushedDate
                                }
                            }
                        }
                        reviews(last: 50) {
                            nodes {
                                author {
                                    login
                                }
                                state
                                createdAt
                            }
                        }
                        reviewRequests(first: 10) {
                            nodes {
                                requestedReviewer {
                                    ... on User {
                                        login
                                    }
                                }
                            }
                        }
                    }
                }
            }
            pageInfo {
                endCursor
                hasNextPage
            }
        }
    }
}
"""
    result = query_github(query, org, states)
    for repo in result:
        if repo['pullRequests']['nodes']:
            yield {
                'name': repo['name'],
                'pullRequests': repo['pullRequests']['nodes'],
            }


def to_slack_user(github_username, mention=True):
    if github_username in REVIEWERS:
        if mention:
            return REVIEWERS[github_username][0]
        return REVIEWERS[github_username][1]
    return github_username


def to_datetime(string):
    if string:
        return datetime.strptime(string, '%Y-%m-%dT%H:%M:%SZ')


def to_days_ago(date, today=datetime.today()):
    return (today - date).days


class RequestCallFailedException(Exception):
    """A custom Exception class that is raised when HTTP calls fail"""
    pass


class PullRequest:
    @classmethod
    def from_api(cls, **struct):
        self = cls()
        self.reviews = Review.from_api(self, **struct.pop('reviews'))
        self.review_requests = ReviewRequest.from_api(
            **struct.pop('reviewRequests'))
        self.pushed_date = to_datetime(
            struct.pop('commits')['nodes'][0]['commit']['pushedDate'])
        struct['createdAt'] = to_datetime(struct['createdAt'])
        struct['updatedAt'] = to_datetime(struct['updatedAt'])
        if not self.pushed_date:
            self.pushed_date = struct['updatedAt']
        struct['author'] = struct.pop('author')['login']
        self.fields = struct
        self.age = to_days_ago(self.fields['updatedAt'])
        self.should_display = self.age < MAX_PR_AGE and \
                              (self.fields['author'] in DEVELOPERS or
                               self.fields['author'] in BOTS and
                               self.fields['repo_name'] in BOTS[self.fields['author']])
        self.wip = self.fields['title'].startswith('WIP')
        self.isDraft = self.fields['isDraft']
        return self

    def newer_than(self, time):
        return self.pushed_date > time or any(
            r.fields['author'] == self.fields['author']
            and r.fields['createdAt'] > time for r in self.reviews)

    def display_author(self):
        return to_slack_user(self.fields['author'],
                             mention=self.author_actionable())

    def author_actionable(self):
        return self.wip or (
                not self.review_requests and
                not any(r.pending() for r in self.reviews))

    def __str__(self):
        s = """\
{user} submitted <{url}|{repo_name}#{num} _{title}_>, updated {age} ago:
""".format(user=self.display_author(),
           repo_name=self.fields['repo_name'],
           num=self.fields['number'],
           title=self.fields['title'],
           age=(self.age == 1 and '1 day' or '{} days'.format(self.age)),
           url=self.fields['url'])
        if self.reviews:
            s += '    - Reviewed by: {}\n'.format(', '.join(
                str(r) for r in self.reviews
                if r.fields['author'] != self.fields['author']))
        s += '    - Pending reviews from: {}'.format(
            ', '.join(str(r) for r in self.review_requests) or 'N/A')
        return s


class Review:
    @classmethod
    def from_api(cls, pull_request, **struct):
        states = {}
        created_at = {}
        results = []
        for r in struct['nodes']:
            author = r['author']['login']
            if states.get(author, 'COMMENTED') == 'COMMENTED':
                states[author] = r['state']
            if r['createdAt'] > created_at.get(author, ''):
                created_at[author] = r['createdAt']
        for author in states:
            self = cls()
            results.append(self)
            self.fields = {
                'author': author,
                'createdAt': to_datetime(created_at[author]),
                'state': states[author],
            }
            self.pull_request = pull_request
        return results

    def pending(self):
        return self.fields['state'] != 'APPROVED' and \
               self.pull_request.newer_than(self.fields['createdAt']) and \
               not self.pull_request.wip and \
               self.fields['author'] != self.pull_request.fields['author']

    def __str__(self):
        if self.pending():
            user = to_slack_user(self.fields['author'])
        else:
            user = to_slack_user(self.fields['author'], mention=False)
        return '{} ({})'.format(user, self.fields['state'])


class ReviewRequest:
    @classmethod
    def from_api(cls, **struct):
        results = []
        for r in struct['nodes']:
            results.append(cls())
            results[-1].fields = r
        return results

    def __str__(self):
        # Sometimes the self.fields['requestedReviewer'] is None so I return Unknown in that case.
        # There might be another better approach to it.
        return to_slack_user(
            self.fields['requestedReviewer']['login']) if self.fields and 'requestedReviewer' in self.fields and \
                                                          self.fields['requestedReviewer'] else 'Unknown'


prs = []
for org in ORGANIZATIONS:
    for repo in get_open_prs(org, 'OPEN'):
        for pull_request in repo['pullRequests']:
            pr = PullRequest.from_api(repo_name=repo['name'], **pull_request)
            if pr.should_display:
                prs.append(pr)

draft_prs = list(filter(lambda pr: pr.isDraft, prs))
outstanding_prs = list(filter(lambda pr: not pr.isDraft, prs))

print("*Outstanding Pull Requests*")
if len(outstanding_prs) == 0:
    print("No outstanding Pull Requests")

outstanding_prs.sort(key=lambda a: a.age)
for pr in outstanding_prs:
    print(str(pr))

print("*Draft Pull Requests*")
if len(draft_prs) == 0:
    print("No draft Pull Requests")

draft_prs.sort(key=lambda a: a.age)
for pr in draft_prs:
    print(str(pr))

print("<https://github.com/pulls/review-requested|PRs for you to review>")
print("<https://github.com/openstax/ce-reports|Source Code>")
