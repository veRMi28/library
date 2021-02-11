"""
inputs:
    - json.commit_sha:
        type: str
        required: False
        doc: The commit_sha to fetch. If missing `origin/master` will be fetched.
"""

import os
import re
import yaml
import base64
import flow_api


def handler(system: flow_api.System, this: flow_api.Execution):
    """
    Clone a git repository, create Cloudomation objects from the files.
    All .py files in the flows/ subdirectory will be stored as Flows.
    All .yaml files in the settings/ subdirectory will be stored as Settings.
    All files in the files/ subdirectory will be stored as Files.
    """
    git_repository = None


    # Ask the user in a Popup message, if a path for a vault secret
    # to the repository exists:
    vault_path = system.message(
        subject='Git Repository info',
        message_type = 'POPUP',
        body={
            'type': 'object',
            'properties': {
                'path': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'If you have credentials for your repository saved in a vault, enter the path here: ',
                    'example': '/somepath/my-gitlab',
                    'order': 1,
                },
                'repository url': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the URL for the repository you want to clone in to Cloudomation:',
                    'example': 'https://my-vault-host:8200',
                    'order': 2,
                },
                'Ok': {
                    'element': 'submit',
                    'label': 'OK',
                    'type': 'boolean',
                    'order': 3,
                },
            },
        },
    ).wait().get('response')

    # use the given vault-path and repository-URL:
    git_repository = vault_path.get('repository url', None)
    vault_path = vault_path.get('path', None)
    if vault_path is not None:
        # if it exists, get the secrets for the repository:
        git_login_form_response = this.connect(
            'vault',
            name='fetch gitlab-token',
            path='gitlab-token',
        ).get('output_value')['result']['data']['data']
        git_username = git_login_form_response['username'] 
        git_password = git_login_form_response['password']
        # # EXAMPLE: read a secret
        # secret_value = this.task(
        #     'VAULT',
        #     host='https://my-vault-host:8200',
        #     path='/v1/secret/data/my-secret',
        #     version=None,  # read latest version
        #     token='my-vault-token',
        # ).get('output_value')['result']['data']['data']
        # assert secret_value == {'secret-key': 'secret-value'}
    else:
        # otherwise, ask user to add new credentials for a repository
        git_login_form_response = system.message(
            subject='Git Repository info',
            message_type = 'POPUP',
            body={
                'type': 'object',
                'properties': {
                    'username': {
                        'element': 'string',
                        'type': 'string',
                        'label': 'What is your username for the GIT repository?',
                        'order': 1,
                    },
                    'password': {
                        'element': 'password',
                        'type': 'string',
                        'label': 'What is your password for the GIT repository?',
                        'order': 2,
                    },
                    'repository name': {
                        'element': 'string',
                        'type': 'string',
                        'label': 'Enter the URL for the repository you want to clone in to Cloudomation:',
                        'default': git_repository,
                        'order': 3,
                    },
                    'token_label': {
                        'element': 'markdown',
                        'description': 'To interact with your string account via the string REST API, you need to supply a string token for your account.\nPlease go to [https://github.com/settings/tokens](https://github.com/settings/tokens){ext} and generate a personal access token.\nCheck the following options: repo and admin:repo_hook.\nPaste the token here after you have created it.',
                        'order': 4,
                    },
                    'token': {
                        'element': 'string',
                        'type': 'string',
                        'label': 'GitHub token:',
                        'order': 5,
                    },
                    'add_to_vault': {
                        'element': 'toggle',
                        'type': 'boolean',
                        'label': 'Adding credentials to the vault?:',
                        'order': 6,
                    },
                    'Ok': {
                        'element': 'submit',
                        'label': 'OK',
                        'type': 'boolean',
                        'order': 7,
                    },
                },
                'required': [
                    'username',
                    'password',
                    'repository name',
                ],
            },
        ).wait().get('response')
        git_username = git_login_form_response['username'] 
        git_password = git_login_form_response['password']
        git_repository = git_login_form_response['repository name']
        add_to_vault = git_login_form_response.get('add_to_vault', False)

        if add_to_vault:
            vault_response = system.message(
                subject='Add credentials to your Vault',
                message_type = 'POPUP',
                body={
                    'type': 'object',
                    'properties': {
                        'host': {
                            'element': 'string',
                            'type': 'string',
                            'label': 'Where is your Vault hosted?',
                            'example': 'https://my-vault-host:8200',
                            'order': 1,
                        },
                        'path': {
                            'element': 'string',
                            'type': 'string',
                            'label': 'Enter a path for your Vault entry (e.g. user1-gitlab):',
                            'example': 'user1-gitlab',
                            'order': 2,
                        },
                        'token': {
                            'element': 'string',
                            'type': 'string',
                            'label': 'Enter your token for the vault:',
                            'order': 3,
                        },
                        'Ok': {
                            'element': 'submit',
                            'label': 'OK',
                            'type': 'boolean',
                            'order': 4,
                        },
                    },
                    'required': [
                        'host',
                        'path',
                        'token',
                    ],
                },
            ).wait().get('response')
            # create a secret in vault
            this.task(
                'VAULT',
                host=vault_response.get('host', None),
                path=vault_response.get('path', None),
                token=vault_response.get('token', None),
                data={
                    'password': git_password,
                    'username': git_username,
                },
            )

    # Check the repository url: 
    if len(re.split("//?", git_repository)) != 4:
        git_login_form_response = system.message(
            subject='Warning: wrong url',
            message_type = 'POPUP',
            body={
                'type': 'object',
                'properties': {
                    'error': {
                        'element': 'markdown',
                        'description': (f'The given repository URL is not of form: \
                            https://repository.url/user/repository\n\
                            You provided: {git_repository}\n\
                            Please restart this scipt for a second chance!'),
                        'order': 1,
                    },
                    'Ok': {
                        'element': 'submit',
                        'label': 'OK',
                        'order': 2,
                    },
                },
            },
        ).wait().get('response')
        return this.success('Please restart this scipt for a second chance, see warning!')
        
    inputs = this.get('input_value')
    this.set_output('inputs', inputs)
    # this flow is registered as webhook, triggered by a commit to the
    # repository. The commit sha is passed in .json.commit_sha
    # when started manually, it will sync from master
    if git_repository is None:
        repo = inputs.get('repo')
        if not repo:
            repo = 'flows'
        git_repository = f'https://gitlab.com/cloudomation/{repo}.git'
    ref = inputs.get('branch')
    if not ref:
        try:
            ref = inputs['json']['commit_sha']
        except (KeyError, TypeError):
            ref = 'develop'

    repo_info = {
        'repository_url': f'{git_repository}'
        # 'repository_url': f'https://gitlab.com/cloudomation/{repo}.git'
    }
    # the git 'get' command fetches the content of the repository.
    # since no files_path is passed, the files will be returned in the
    # output_value of the task
    reference_list = [ref, 'develop', 'master']
    files = None
    for reference in reference_list:
        try:
            files = this.task(
                'GIT',
                command='get',
                repository_url=repo_info['repository_url'],
                httpCookie=repo_info.get('httpCookie'),
                ref=reference,
                username=git_username,
                password=git_password,
            ).get('output_value')['files']
        except flow_api.exceptions.DependencyFailedError:
            files = None
            if reference == reference_list[-1]:
                raise
            # # assuming the branch does not exist, fetching default branch
            # files = this.task(
            #     'GIT',
            #     command='get',
            #     repository_url=repo_info['repository_url'],
            #     httpCookie=repo_info.get('httpCookie'),
            #     username=gitlab_username,
            #     password=gitlab_password,
            # ).get('output_value')['files']
        else:
            break

  
    this.set_output('git_files', files)
    return this.success('all done')

    # iterate over all files
    for file_ in files:
        # split the path and filename
        path, filename = os.path.split(file_['name'])
        # split the filename and file extension
        name, ext = os.path.splitext(filename)
        if 'flows' in path and ext == '.py':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # create or update Flow object
            system.flow(name).save(script=text_content)
        elif 'settings' in path and ext == '.yaml':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # load the yaml string in the file content
            value = yaml.safe_load(text_content)
            # create or update Setting object
            system.setting(name).save(value=value)
        elif 'files' in path:
            # create or update File object
            # we use the name with the extension
            # pass the base64 encoded binary file content directly
            system.file(filename).save(content=file_['content'], convert_binary=False)

    return this.success('all done')
