def handler(system, this):
    inputs = this.get('input_value')
    message_id = inputs['message_id']
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
