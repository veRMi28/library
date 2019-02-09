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

def handler(system, this):

    github_account_exists = this.task(
        'INPUT',
        request=(
            'Do you have a github account? Please answer y for yes or n for no'
        )
    ).run()

    if github_account_exists.get('output_value')['response'] == 'n':
        this.task(
            'INPUT',
            request=(
                'Please go to https://github.com/join and create an account.'
            )
        ).run()

    elif github_account_exists.get('output_value')['response'] == 'y':
        github_un_request = this.task(
            'INPUT',
            request=('What is your github username?')
        ).run()
        github_username = github_un_request.get('output_value')['response']

        github_token_request = this.task(
            'INPUT',
            request=(
                'To interact with your github account via the github REST API,'
                ' we need a github token for your account. Please go to '
                'https://github.com/settings/tokens and generate a personal '
                'access token. Check the following options: repo and '
                'admin:repo_hook. Paste the token here after you have created '
                'it.'
            )
        ).run()
        github_token = github_token_request.get('output_value')['response']

        github_repo_exists = this.task(
            'INPUT',
            request=(
                'Do you have a github repository you would like to use for '
                'your flow scripts? Please answer y for yes or n for no. If '
                'you answer n, we will set up a new repository for you.'
            )
        ).run()
        this.log(github_repo_exists.get('output_value')['response'])

        if github_repo_exists.get('output_value')['response'] == 'y':
            github_repo_name_request = this.task(
                'INPUT',
                request=('What is the name of your github repository?')
            ).run()
            github_repo_name = (
                github_repo_name_request.get('output_value')['response']
            )

        elif github_repo_exists.get('output_value')['response'] == 'n':
            github_repo_name_request = this.task(
                'INPUT',
                request=(
                    'We will now set up a github repository for you. '
                    'What should be the name of the repository?'
                )
            ).run()
            github_repo_name = (
                github_repo_name_request.get('output_value')['response']
            )

            github_desc_request = this.task(
                'INPUT',
                request=(
                    'Please describe your repository briefly. '
                    'This description will be published on your '
                    'github repository page, where you can change '
                    'it later.'
                )
            ).run()
            github_repo_description = (
                github_desc_request.get('output_value')['response']
            )

            private_repo_request = this.task(
                'INPUT',
                request=(
                    'Do you want to create a private repository? Please '
                    'respond true to create a private repository or false to '
                    'create a public repository. After you respond, your '
                    'repository will be created. Please check the outputs of '
                    'this execution to see if the repository was created '
                    'successfully.'
                )
            ).run()
            private_repo = private_repo_request.get('output_value')['response']

            homepage = (
                f'https://github.com/{github_username}/{github_repo_name}'
            )

            this.task(
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
            ).run()
            this.log(
                f'Github repository created successfully. '
                f'Check it out here: {homepage}'
            )

        else:
            this.task(
                'INPUT',
                request=(
                    'We did not recognise your response. '
                    'Please restart the flow script and try again.'
                ),
                timeout=0.2
            ).run()

        github_info = {
            'github_username': github_username,
            'github_repo_name': github_repo_name,
            'github_token': github_token
        }

        system.setting(name='github_info', value=github_info)
        this.set_output('github_info', github_info)

    else:
        this.task(
            'INPUT',
            request=(
                'We did not recognise your response. '
                'Please restart the flow script and try again.'
            ),
            timeout=0.2
        ).run()

    return this.success('All done.')
