import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # create a secret
    this.task(
        'VAULT',
        host='https://my-vault-host:port',
        secret_path='my-secret',
        data={
            'secret-key': 'secret-value',
        },
        token='my-vault-token',
    )

    # read a secret
    secret_value = this.task(
        'VAULT',
        host='https://my-vault-host:port',
        secret_path='my-secret',
        version=None,  # read latest version
        token='my-vault-token',
    ).get('output_value')['result']['data']['data']
    assert isinstance(secret_value, dict)

    # destroy all versions of secret
    this.task(
        'VAULT',
        host='https://my-vault-host:port',
        secret_path='my-secret',
        mode='delete_metadata',
        token='my-vault-token',
    )

    return this.success('all done')
