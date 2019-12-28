"""
This flow script changes the password of an user.
"""


def handler(system, this):
    inputs = this.get('input_value')
    user_name = inputs.get('user_name', 'nobody')

    response = system.message(
        subject='Change user password',
        body={
            'type': 'object',
            'properties': {
                'user_name': {
                    'element': 'string',
                    'type': 'string',
                    'example': 'Sam Sample',
                    'default': user_name,
                    'label': 'User name',
                    'order': 1,
                },
                'current_password': {
                    'element': 'password',
                    'type': 'string',
                    'label': 'Current password',
                    'order': 2,
                },
                'current_password_label': {
                    'element': 'markdown',
                    'description': '<i class="fa fa-info fa-fw text-info"></i> Client admins are not required to specify the current password',
                    'order': 3,
                },
                'new_password': {
                    'element': 'password',
                    'type': 'string',
                    'label': 'New password',
                    'order': 4,
                },
                'new_password_check': {
                    'element': 'password',
                    'type': 'string',
                    'label': 'New password (again)',
                    'order': 5,
                },
                'ok': {
                    'element': 'submit',
                    'type': 'boolean',
                    'label': 'Ok',
                    'order': 6,
                },
            },
            'required': [
                'user_name',
                'new_password',
                'new_password_check',
            ],
        }
    ).wait().get('response')

    if response['new_password'] != response['new_password_check']:
        return this.error('passwords did not match')

    if 'current_password' in response:
        system.user(response['user_name']).save(
            current_password=response['current_password'],
            password=response['new_password'],
        )
    else:
        system.user(response['user_name']).save(
            password=response['new_password'],
        )

    this.success('all done')
