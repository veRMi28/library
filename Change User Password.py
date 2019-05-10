"""
This flow script changes the password of an user.

It queries the current and new password and sends a PATCH request
to the cloudomation.com API.
"""


def handler(system, this):
    inputs = this.get('input_value')
    user_name = inputs.get('user_name', 'nobody')

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
    execution = this.flow(
        'Input Form',
        questions=questions,
        init=dict(
            protect_outputs=['responses']  # protect responses,
                                           # they contain a password
        ),
    ).run()
    outputs = execution.get('output_value')
    resp = outputs['responses']

    if resp['new_password'] != resp['new_password_check']:
        return this.error('passwords did not match')

    patch = {
        'current_password': resp['current_password'],
        'password': resp['new_password']
    }

    # Send change password request
    instance = system.get_env_name()
    request = {
        'url': f'https://{instance}.cloudomation.com/api/1/user/{user_name}',
        'method': 'patch',
        'data': patch
    }
    execution = this.task(
        'REST',
        input_value=request,
        pass_user_token=True,
        init=dict(
            protect_inputs=['data']
        ),
    ).run()
    this.success('all done')
