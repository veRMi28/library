"""
Call an Apache Cloud Stack API endpoint and save the result in the outputs

inputs:
    - command:
        type: dict
        required: True
        doc: dict which contains the acutal command and the apikey e.g.: { 'command': 'deployVirtualMachine', 'apikey': 'your-api-key' }
    - secret:
        type: string
        required: True
        doc: the api secret
    - compute_endpoint:
        type: string
        required: True
        doc: the URL of the apache cloud stack endpoint
outputs:
    result:
        type: dict
        doc: the result json of the api key as dict
"""

def handler(system, this):

    # retrieve the necessary inputs and store them in local variables
    inputs = this.get('input_value')
    command = inputs.get('command')
    secret = inputs.get('secret')
    compute_endpoint = inputs.get('compute_endpoint')

    # sign the api call using acs.sign flow script
    query_str = this.flow(
        'acs.sign',
        input_value={
            'command':command,
            'secret':secret,
        },
        name=f'sign {command.get("command")}',
    ).get('output_value')['query_str']

    # make the actual call using cloudomation REST task
    result = this.task(
        'REST',
        url=f'{compute_endpoint}?{query_str}',
        name=f'REST call {command.get("command")}',
    ).get('output_value').get('json')
    
    # save the result in the outputs
    this.save(output_value={'result': result})
    return this.success('all done')