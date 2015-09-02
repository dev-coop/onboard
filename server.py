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
    return github_request(
        'PUT',
        '/orgs/%s/memberships/%s' % (env['GITHUB_ORGANIZATION_NAME'], github_username),
        data=json.dumps({"role": "member"})
    )


def slack_invite(email):
    return request_post(
        'https://%s.slack.com/api/users.admin.invite' % (env['SLACK_TEAM_NAME']),
        data=json.dumps({
            "token": env['SLACK_API_TOKEN'],
            "email": email,
            "set_active": True,
        }),
        headers={
            'Content-type': 'application/json',
            'Accept': 'text/plain'
        }
    )


# ----------------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------------
@post('/add')
def add():
    # Parse input
    if request.forms.get('token') != env['SLACK_API_TOKEN']:
        # Make sure we got a request from the actual slack server not some ass hole
        return HTTPError(status=403)

    text = request.forms.get('text')
    if not text or len(text.split(' ')) != 2:
         response.status_code = 400
         return {"error": "Invalid text input, should look like /onboard <github name>; <email>"}

    github_username, email = text.split(' ')
    github_username = github_username.strip()
    email = email.strip()

    # Add to github
    resp = github_add_member_to_org(github_username)
    if resp.status_code != 200:
        response.status_code = 500
        return {"error": "Bad response from Github (%s): %s" % (resp.status_code, resp.content)}

    # Add to slack
    resp = slack_invite(email)
    if resp.status_code != 200:
        response.status_code = 500
        return {"error": "Bad response from Slack (%s): %s" % (resp.status_code, resp.content)}

    # Add to screenhero
    # TODO
    return "Successfully added user to Github, Slack and Screenhero... wee!"


@get("/")
def nice_index():
    return "Hello, I am an <a href='https://github.com/dev-coop/onboard'>onboarding bot</a>!"


# ----------------------------------------------------------------------------
# Server
# ----------------------------------------------------------------------------
# Heroku sets PORT env var
run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
