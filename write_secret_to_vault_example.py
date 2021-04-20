import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    secrets_input_form = system.message(
        subject='Input for a secret with username and password',
        message_type = 'POPUP',
        body={
            'type': 'object',
            'properties': {
                'username': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the secret "username":',
                    'order': 1,
                },
                'password': {
                    'element': 'password',
                    'type': 'string',
                    'label': 'Enter the secret "password":',
                    'order': 2,
                },
                'Ok': {
                    'element': 'submit',
                    'label': 'OK',
                    'type': 'boolean',
                    'order': 3,
                },
            },
            'required': [
                'username',
                'password',
            ],
        },
    ).wait().get('response')

    target_vault = '<your-vault-configuration-name>' # if None, then is iterating over all vaults in DB
    secret_path = '<your-secret-path-in-vault>'
    new_secrets = {
        "password": secrets_input_form['username'],
        "username": secrets_input_form['password'],
    }

    my_vault = system.vault_config(target_vault)
    my_vault.write_secret(
        secret_path,
        new_secrets,
    )
    return this.success('all done')
