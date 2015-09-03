import json
import os

from bottle import get, run, post, request, HTTPError, response
from requests import Session
from requests import post as request_post


# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
env_var_names = (
    'GITHUB_API_KEY',
    'GITHUB_ORGANIZATION_NAME',
    'GITHUB_ONBOARD_TEAM_NAME',
    'SLACK_API_TOKEN',
    'SLACK_API_SECRET',
    'SLACK_TEAM_NAME',
)
env = {}
for name in env_var_names:
    env[name] = os.environ.get(name, None)
    assert env[name], "Missing environment variable: %s" % name


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def github_request(method, endpoint, data=None):
    github_session = Session()
    github_session.auth = (env['GITHUB_API_KEY'], 'x-oauth-basic')
    base_url = 'https://api.github.com'
    method_func = getattr(github_session, method.lower())
    response = method_func(
        base_url + endpoint,
        data=data
    )
    return response


def github_add_member_to_org(github_username):
    # Get list of teams
    resp = github_request(
        'GET',
        '/orgs/%s/teams' % env['GITHUB_ORGANIZATION_NAME']
    )

    if resp.status_code != 200:
        return resp

    team_id = 0
    for team in resp.json():
        if team['name'].lower() == env['GITHUB_ONBOARD_TEAM_NAME'].lower():
            team_id = team['id']

    if team_id == 0:
        raise Exception("Team not found!")

    return github_request(
        'PUT',
        '/teams/%s/memberships/%s' % (team_id, github_username),
        data=json.dumps({"role": "member"})
    )


def slack_invite(email):
    return request_post(
        'https://%s.slack.com/api/users.admin.invite' % (env['SLACK_TEAM_NAME']),
        data={
            "token": env['SLACK_API_TOKEN'],
            "email": email,
            "set_active": True,
        }
    )


# ----------------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------------
@post('/add')
def add():
    success_messages = []
    error_messages = []

    # Parse input
    if request.forms.get('token') != env['SLACK_API_SECRET']:
        # Make sure we got a request from the actual slack server not some ass hole
        response.status = 403
        return "Invalid SLACK_API_TOKEN received, does not match. Received %s" % request.forms.get('token')

    text = request.forms.get('text')
    if not text or len(text.split(' ')) != 2:
         response.status = 400
         return "Invalid text input, should look like /onboard <github name>; <email>"

    github_username, email = text.split(' ')
    github_username = github_username.strip()
    email = email.strip()

    # Add to github
    resp = github_add_member_to_org(github_username)
    if resp.status_code == 200:
        success_messages.append("Added to GitHub")
    else:
        error_messages.append("Bad response from Github (%s): %s" % (resp.status_code, resp.content))

    # Add to slack
    resp = slack_invite(email)
    if resp.status_code != 200:
        error_messages.append("Bad response from Slack (%s): %s" % (resp.status_code, resp.content))
    elif "error" in resp.json():
        error_messages.append("Bad response from Slack (%s): %s" % (resp.status_code, resp.json()["error"]))
    else:
        success_messages.append("Added to Slack")

    # TODO: Add to screenhero
    response_text = ''

    if len(success_messages) != 0:
        success_concated = '\n'.join(success_messages)
        response_text += "Successful:\n" + success_concated + '\n\n'

    if len(error_messages) != 0:
        errors_concated = '\n'.join(error_messages)
        response_text += "Failed:\n" + errors_concated

    return response_text


@get("/")
def nice_index():
    return "Hello, I am an <a href='https://github.com/dev-coop/onboard'>onboarding bot</a>!"


# ----------------------------------------------------------------------------
# Server
# ----------------------------------------------------------------------------
# Heroku sets PORT env var
run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
