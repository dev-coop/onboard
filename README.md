# onboard
a slack integration for adding team members to github, slack, and screenhero. hosted on heroku


# Setup

### Env vars

```bash
export PORT=5000

export GITHUB_ORGANIZATION_NAME=the_gang
export GITHUB_API_KEY=1234567890
export GITHUB_ONBOARD_TEAM_NAME=Underlings

export SLACK_API_TOKEN=1234567890  # the key you'd use to talk to Slack API
export SLACK_API_SECRET=1234567890  # the key Slack sends to us to verify it's really Slack
export SLACK_TEAM_NAME=paddys_pub
```

### Run

```bash
python server.py
``` 

It will start running on the port specified by the `PORT` env var or default `5000`


# Usage on slack

`/onboard <github username> <email>`
