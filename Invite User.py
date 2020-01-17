"""
This flow script invites an user to cloudomation.

It queries the name and email address of the new user and creates a user
object. The new user has to validate the email address by clicking on the
activation link. The new user also has to set a password.
"""


def handler(system, this):
    inputs = this.get('input_value')
    message_id = inputs.get('message_id')

    if message_id is None:
        # Query user details
        message = system.message(
            subject='Invite a new user to join your client',
            body={
                'type': 'object',
                'properties': {
                    'name_info': {
                        'element': 'markdown',
                        'example': 'Please enter a login name of the user you want to invite',
                        'order': 1,
                    },
                    'name': {
                        'element': 'string',
                        'type': 'string',
                        'example': 'newuser',
                        'maxLength': 32,
                        'label': 'User name',
                        'order': 2,
                    },
                    'email_info': {
                        'element': 'markdown',
                        'example': (
                            'Please enter the email address of the user you want to invite.'
                            'The user will receive an email with a link to accept the invitation.'
                        ),
                        'order': 3,
                    },
                    'email': {
                        'element': 'string',
                        'type': 'string',
                        'format': 'email',
                        'example': 'user@domain.com',
                        'label': 'Email address',
                        'order': 4,
                    },
                    'Send invitation': {
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 5,
                    },
                },
                'required': [
                    'name',
                    'email',
                ],
            }
        )
        message_id = message.get('id')
        this.save(output_value={
            'message_id': message_id,
        })
        this.flow(
            'Invite User',
            message_id=message_id,
            wait=False,
        )
        return this.success('requested new user details')

    message = system.message(message_id)
    response = message.wait().get('response')
    this.log(response=response)

    # Create user object
    system.user(
        select=None,
        name=response['name'],
        pending_email=response['email'],
    )

    # Success
    return this.success(f'{response["name"]} was invited to cloudomation')
