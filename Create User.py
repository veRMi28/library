"""
This flow script creates an user object.

It queries for the details of the new user, and then sends a POST
request to the cloudomation.io API. Credentials of the user executing
the flow script will be used to authenticate against the
cloudomation.io API.
"""


def handler(system, this):
    # Query user details
    questions = {
        'name': {
            'label': 'New user name',
        },
        'email': {
            'label': 'New user email address',
        },
        'password': {
            'label': 'New user password',
            'type': 'password',
        },
    }
    execution = this.flow(
        'Input Form',
        questions=questions,
        init=dict(
            protect_outputs=['responses'],  # protect responses,
                                            # they contain a password
        ),
    ).run()
    outputs = execution.get('output_value')
    user = outputs['responses']  # the responses dict is the user

    # Send user creation request
    instance = system.get_env_name()
    request = {
        'url': f'https://{instance}.cloudomation.io/api/1/user',
        'method': 'post',
        'data': user
    }
    execution = this.task(
        'REST',
        input_value=request,
        pass_user_token=True,
        init=dict(
            protect_inputs=['data'],
        ),
    ).run()
    user_id = execution.get('output_value')['json']['id']

    # Success
    this.log(
        f'user "{user["name"]}" '
        f'with ID "{user_id}" '
        'was created successfully'
    )
