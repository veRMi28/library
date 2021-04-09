# This flow script does two things:
# 1. it sets up a webhook on Cloudomation which is then used to subscribe to a
# github webhook
# 2. it sets up a github webhook which pushes events from a github repo to the
# Cloudomation webhook

# The Cloudomation webhook is set to trigger a flow script that synchronises
# flow scripts and settings from a github repo to Cloudomation whenever there
# is a push to the github repository.

# If you have a setting called "github_info", this flow script will assume that
# it contains three values: your github username, the name of the github repo
# you want to synchronise with Cloudomation, and a github access token which
# enables the flow script to configure a webhook for your github repo. If the
# setting doesn't exist, it will start a secod flow script called
# "request_github_info" which is alo available in the public flow script
# library. This second flow script will ask you about your github info and if
# you want, it will create a github repository for you.

# The actual synchronisation of flow scripts and settings from github to your
# Cloudomation client account is done by a third flow script called
# "sync_from_github". It's also available in the public flow script library.

# For this process to work, you need the following three flow scripts:
# 1. configure_webhoooks_github_cloudomation (this one)
# 2. request_github_info
# 3. sync_from_github

# Enjoy :)


import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # (1) Set up a Cloudomation webhook
    # which triggers a flow script which synchronises settings and flow scripts
    # from a github repo

    # check if the webhook exists
    if not system.setting('client.webhook.github_sync').exists():
        # If it doesn't exist, we create it.
        # First, we ask the user for a github authorisation key:
        c_webhook_key_request = system.message(
            subject='Github authorisation key',
            message_type = 'POPUP',
            body={
                'type': 'object',
                'properties': {
                    'key': {
                        'label': (f'Please specify an authorization key for the '
                                 'Cloudomation webhook. Can be any alphanumeric '
                                  'string.'),
                        'element': 'string',
                        'type': 'string',
                        'order': 1,
                    },
                    'start': {
                        'label': 'OK',
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 2,
                    },
                },
                'required': [
                    'key',
                ],
            },
        ).wait()

        c_webhook_key = c_webhook_key_request.get('response')['key']

        # Second, we read out the user's name from this execution record.
        # Note that this will set up a webhook with the user rights of
        # the user who is executing this flow script.
        cloudomation_username = system.get_own_user().get('name')

        system.setting(
            name='client.webhook.github_sync',
            value={
                "flow_name": "sync_from_github",
                "user_name": cloudomation_username,
                "key": c_webhook_key
            }
        )
    else:
        c_webhook_key = (
            system.setting('client.webhook.github_sync').load('value')['key']
        )

    # (2) Set up a github webhook
    # which pushes events from a repository to the Cloudomation webhook

    # check if github info setting exists
    # if it doesn't, start the flow script to request info from user
    if not system.setting('github_info').exists():
        this.flow('request_github_info')

    github_info = system.setting('github_info').load('value')
    github_username = github_info['github_username']
    github_repo_name = github_info['github_repo_name']
    github_token = github_info['github_token']

    # Check if the webhook already exists. To do that, we call the
    # github REST API to list all existing webhooks for your repository.
    github_webhook_endpoint = (
        f'https://api.github.com/repos/'
        f'{github_username}/'
        f'{github_repo_name}/'
        f'hooks'
    )

    list_github_webhooks = this.task(
        'REST',
        url=github_webhook_endpoint,
        headers={
            'Authorization': f'token {github_token}'
        },
    )

    # we get the response
    github_list_webhook = list_github_webhooks.get('output_value')['json']

    # and we check if our webhook already exists
    cloudomation_client_name = system.get_own_client().get('name')
    c_webhook_url = (
        f'https://app.cloudomation.com/api/latest/webhook/'
        f'{cloudomation_client_name}/'
        f'github_sync?'
        f'key={c_webhook_key}'
    )

    webhook_exists = False

    for webhook in github_list_webhook:
        if webhook['config']['url'] == c_webhook_url:
            webhook_exists = True
            break

    this.set_output('webhook_exists', webhook_exists)

    # if the webhook doesn't already exist, we create it
    if not webhook_exists:
        this.task(
            'REST',
            url=github_webhook_endpoint,
            method='POST',
            data={
              'events': [
                'push'
              ],
              'config': {
                'url': c_webhook_url,
                'content_type': 'json'
              }
            },
            headers={
                'Authorization': f'token {github_token}'
            },
        )
        this.set_output('webhook_created', 'true')

    return this.success('All done - Cloudomation and github webhooks set up.')
