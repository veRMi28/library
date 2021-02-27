# This flow script requests information about your github repository and
# guides you through the process of setting up a repository, if you want. It
# will store all information about your github repository in a setting called
# "github_info". This setting can then be used by other flow scripts that
# interact with your github repository.

# You can run it manually to create a github repo, or use it together with
# another flow script called configure_webhooks_github_cloudomation to set
# up a webhook on Cloudomation and github which will synchronise your flow
# scripts and settings automatically from your github repository with
# Cloudomation whenever there is a push to the repository.

# For the actual synchronisation of flow scripts, once your webhook is set
# up, you need a third flow script: sync_from_github. All are available in
# the public flow script library.

# For this process to work, you need the following three flow scripts:
# 1. configure_webhoooks_github_cloudomation
# 2. request_github_info (this one)
# 3. sync_from_github


import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    github_form_response = system.message(
        subject='GitHub info',
        message_type = 'POPUP',
        body={
            'type': 'object',
            'properties': {
                'username': {
                    'label': 'What is your GitHub username?',
                    'element': 'string',
                    'type': 'string',
                    'order': 1,
                },
                'no_username': {
                    'element': 'submit',
                    'type': 'boolean',
                    'label': 'I don\'t have a GitHub account',
                    'order': 2,
                    'required': [],
                },
                'token_label': {
                    'element': 'markdown',
                    'description': 'To interact with your string account via the string REST API, you need to supply a string token for your account.\nPlease go to [https://github.com/settings/tokens](https://github.com/settings/tokens){ext} and generate a personal access token.\nCheck the following options: repo and admin:repo_hook.\nPaste the token here after you have created it.',
                    'order': 3,
                },
                'token': {
                    'element': 'string',
                    'label': 'GitHub token:',
                    'type': 'string',
                    'order': 4,
                },
                'repository name': {
                    'element': 'string',
                    'label': 'Which GitHub repository you would like to use for your flow scripts? If this field is left blank, we will set up a new repository for you.',
                    'type': 'string',
                    'order': 5,
                },
                'Ok': {
                    'element': 'submit',
                    'label': 'OK',
                    'order': 6,
                },
            },
            'required': [
                'username',
                'token',
            ],
        },
    ).wait().get('response')

    if github_form_response.get('no_username'):
        system.message(
            subject='Please create a GitHub account',
            message_type = 'POPUP',
            body={
                'type': 'object',
                'properties': {
                    'message': {
                        'element': 'markdown',
                        'description': 'Please go to [https://github.com/join](https://github.com/join){ext} and create an account. Restart this flow script once you have a GitHub account.',
                        'order': 3,
                    },
                    'submit': {
                        'element': 'submit',
                        'label': 'OK',
                    },
                },
            },
        )
        return this.success('restart this flow when you created a GitHub account')

    github_username = github_form_response['username']
    github_token = github_form_response['token']
    github_repo_name = github_form_response.get('repository name')
    github_repo_exists = github_repo_name is not None

    if not github_repo_exists:
        github_new_repo_response = system.message(
            subject='new GitHub repository',
            message_type = 'POPUP',
            body={
                'type': 'object',
                'properties': {
                    'repository name': {
                        'label': 'We will now set up a GitHub repository for you.\nWhat should be the name of the repository?',
                        'element': 'string',
                        'type': 'string',
                        'order': 1,
                    },
                    'description': {
                        'label': 'Please describe your repository briefly. This description will be published on your GitHub repository page, where you can change it later.',
                        'element': 'string',
                        'type': 'string',
                        'order': 2,
                    },
                    'private_label': {
                        'element': 'markdown',
                        'description': 'Do you want to create a private repository?',
                        'order': 3,
                    },
                    'private repository': {
                        'element': 'toggle',
                        'type': 'boolean',
                        'order': 4,
                    },
                    'Create repository': {
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 5,
                    },
                },
                'required': [
                    'repository name',
                    'description',
                    'private repository',
                ],
            },
        ).wait().get('response')

        github_repo_name = github_new_repo_response['repository name']
        github_repo_description = github_new_repo_response['description']
        private_repo = github_new_repo_response['private repository']
        homepage = f'https://github.com/{github_username}/{github_repo_name}'

        create_repo = this.task(
                'REST',
                url='https://api.github.com/user/repos',
                method='POST',
                data={
                    'name': github_repo_name,
                    'description': github_repo_description,
                    'homepage': homepage,
                    'private': private_repo,
                    'has_issues': 'true',
                    'has_projects': 'true',
                    'has_wiki': 'true',
                    'auto_init': 'true'
                },
                headers={
                    'Authorization': f'token {github_token}'
                },
                run = False,
            )

        try:
            create_repo.run()
        except Exception:
            creation_failed = create_repo.get('output_value')
            this.log(creation_failed)
            system.message(
                subject='Repository creation failed',
                message_type = 'POPUP',
                body={
                    'type': 'object',
                    'properties': {
                        'error': {
                            'element': 'markdown',
                            'description': (f'The creation of your GitHub repository failed with the following error: {creation_failed}'),
                            'order': 1,
                        },
                        'Ok': {
                            'element': 'submit',
                            'label': 'OK',
                            'order': 2,
                        },
                    },
                },
            )

        else:
            system.message(
                subject='Repository creation successful',
                message_type = 'POPUP',
                body={
                    'type': 'object',
                    'properties': {
                        'success': {
                            'element': 'markdown',
                            'description': (f'GitHub repository created successfully. Check it out here: {homepage}'),
                            'order': 1,
                        },
                        'Ok': {
                            'element': 'submit',
                            'label': 'OK',
                            'order': 2,
                        },
                    },
                },
            )

    github_info = {
        'github_username': github_username,
        'github_repo_name': github_repo_name,
        'github_token': github_token
    }

    system.setting(name='github_info', value=github_info)
    this.set_output('github_info', github_info)

    return this.success('all done.')
