# This flow is registered as webhook, triggered by a commit to the
# repository. When started manually, it will sync from master.

# The flow script will sync all files from the github repository specified
# in the "github_info" setting. It will create flow script from all files
# ending with .py and create settings from all files ending with .yaml.

# You can set up the webhooks on github to trigger this flow script using the
# configure_webhooks_github_cloudomation flow script, which is available in the
# public flow script library. You can use another flow script to guide you
# through the process of setting up a github repository. It's called
# request_github_info and is also available in the public flow script library.

# For the full process, you need the following three flow scripts:
# 1. configure_webhoooks_github_cloudomation
# 2. request_github_info
# 3. sync_from_github (this one)

# This flow script is the only one you need continously to syncronise flow
# scripts from your github repository. The other two you need once to set it
# all up.

# Note that once you have this set up, this flow script will ALWAYS check out
# your github repository WHENEVER THERE IS A PUSH. Make sure that you set this
# up to synchronise only a repository that you want to regularly synchronise
# with Cloudomation.

# If you want to stop synchronising files from your github repository with
# Cloudomation, the easiest way is to disable the webhook on github. You can
# also remove or rename the webhook on Cloudomation, but that will lead to
# errors on the side of your github webhook, which will still try to send
# notifications to the Cloudomation webhook.

import os
import yaml
import base64

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # this flow script will sync from the master branch.
    ref = 'master'

    # get the connection information for the github repo
    repo_info = system.setting('github_info').get('value')
    github_username = repo_info['github_username']
    github_repo_name = repo_info['github_repo_name']
    github_token = repo_info['github_token']

    repo_url = (
        f'https://{github_username}:{github_token}@github.com/'
        f'{github_username}/{github_repo_name}.git'
    )

    # the git 'get' command fetches the content of the repository.
    files = this.task(
        'GIT',
        command='get',
        repository_url=repo_url,
        ref=ref,
    ).get('output_value')['files']

    # iterate over all files
    for file_ in files:
        # split the path and filename
        path, filename = os.path.split(file_['name'])
        # split the filename and file extension
        name, ext = os.path.splitext(filename)

        # Create or update flow scripts from all .py files.
        if ext == '.py':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # create or update Flow object
            system.flow(name).save(script=text_content)

        # Create or update settings from all .yaml files.
        elif ext == '.yaml':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # load the yaml string in the file content
            value = yaml.safe_load(text_content)
            # create or update Setting object
            system.setting(name).save(value=value)

        # All files that have a file extension other than .py or .yaml are ignored.

    return this.success('Github sync complete')
