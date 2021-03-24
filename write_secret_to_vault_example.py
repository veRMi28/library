import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # assuming vault API version 2 for KV
    target_vault = 'default_local' # if None, then is iterating over all vaults in DB
    path = 'abcd-test'
    my_secrets = {
        "password": "my-password",
        "username": "user@example.com",
    }
    # my_secrets = {
    #     "data": {
    #         "password": "my-password",
    #         "username": "user@example.com",
    #     }
    # }
    
    my_vault = system.vault_config(target_vault)
    my_vault.write_secret(
        path,
        my_secrets,
    )
    return this.success('all done')
