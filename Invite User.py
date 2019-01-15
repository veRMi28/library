"""
This flow script invites an user to cloudomation.

It queries the name and email address of the new user and creates a user
object. The new user has to validate the email address by clicking on the
activation link. The new user also has to set a password.
"""


def handler(system, this):
    # Query user details
    questions = {
        'name': {
            'label': 'New user name',
        },
        'email': {
            'label': 'Email address of the user to invite',
        },
    }
    responses = this.flow(
        'Input Form',
        questions=questions,
        run=True,
    ).get('output_value')['responses']

    # Create user object
    system.user(
        select=None,
        name=responses['name'],
        email=responses['email'],
    )

    # Success
    this.success(f'{responses["name"]} was invited to cloudomation')
