import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    secret_key_user = 'username'
    secret_key_password = 'password'

    my_connection_name = 'git-example-connection'

    # Create connection of type GIT and link it with vault secrets
    system.connection(my_connection_name).save(
        connection_type='GIT',
        value={
            'username': f'vault.secret({secret_key_user})',
            'password': f'vault.secret({secret_key_password})',
        },
        vault_secrets=[
            {
                'vault_name': 'my-vaultconfig',
                'engine_path': 'my-engine-path',
                'secret_path': 'data/my-git-secret-path',
            },
        ]
    )

    # Use the connection:
    git_metadata = this.connect(
        my_connection_name,
        name='get git-metadata',
        repository_url='https://mygitrepo.com/repo/',
        command='metadata',
    ).get('output_value')
    this.log(git_metadata)

    return this.success('all done')
