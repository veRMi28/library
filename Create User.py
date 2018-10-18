"""
This flow script creates an user object.

It queries for the details of the new user, and then sends a POST
request to the starflows.com API. Credentials of the user executing
the flow script will be used to authenticate against the
starflows.com API.
"""


import json


def handler(c):
    # Query user details
    questions = {
        'name': {
            'label': 'New user name',
        },
        'display_name': {
            'label': 'New user display name',
        },
        'email': {
            'label': 'New user email address',
        },
        'password': {
            'label': 'New user password',
            'type': 'password',
        },
    }
    execution = c.flow(
        'Input Form',
        questions=questions,
        protect_outputs=['responses']  # protect responses,
                                       # they contain a password
    ).run()
    outputs = execution.getOutputs()
    user = outputs['responses']  # the responses dict is the user

    # Send user creation request
    instance = c.getInstance()
    request = {
        'url': f'https://{instance}.cloudomation.io/api/1/user',
        'method': 'post',
        'data': json.dumps(user)
    }
    execution = c.task(
        'REST',
        inputs=request,
        pass_user_token=True,
        protect_inputs=['data']
    ).run()
    user_id = execution.getOutputs()['json']['id']

    # Success
    c.log(
        f'user "{user["name"]}" '
        f'with ID "{user_id}" '
        'was created successfully'
    )
