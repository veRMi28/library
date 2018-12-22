"""
This flow script changes the password of an user.

It queries the current and new password and sends a PATCH request
to the cloudomation.io API.
"""


def handler(c):
    inputs = c.get_inputs()
    user_name = inputs['user_name']

    # Query user details
    questions = {
        'current_password': {
            'label': f'Current password of {user_name}',
            'type': 'password',
        },
        'new_password': {
            'label': f'New password for {user_name}',
            'type': 'password'
        },
        'new_password_check': {
            'label': f'New password for {user_name} (again)',
            'type': 'password',
        },
    }
    execution = c.flow(
        'Input Form',
        questions=questions,
        protect_outputs=['responses']  # protect responses,
                                       # they contain a password
    ).run()
    outputs = execution.get_outputs()
    resp = outputs['responses']

    if resp['new_password'] != resp['new_password_check']:
        return c.error('passwords did not match')

    patch = {
        'current_password': resp['current_password'],
        'password': resp['new_password']
    }

    # Send change password request
    instance = c.get_env_name()
    request = {
        'url': f'https://{instance}.cloudomation.io/api/1/user/{user_name}',
        'method': 'patch',
        'data': patch
    }
    execution = c.task(
        'REST',
        inputs=request,
        pass_user_token=True,
        protect_inputs=['data']
    ).run()
