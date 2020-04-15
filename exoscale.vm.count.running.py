"""
Query how many VMs are running and return count

This example requires a setting with name 'exoscale.api' which contains:
key: your-api-key
secret: your-api-secret
"""

def handler(system, this):
    
    # retrieve the apikey and secret from the system setting
    setting = system.setting('exoscale.api').get('value')
    
    # endpoint to call
    compute_endpoint = "https://api.exoscale.ch/compute"

    # setup command for listing the running VMs
    command = {
        'command': 'listVirtualMachines',
        'state': 'Running',
        'apikey': setting.get('key'),
    }
    result = this.flow(
        'acs.apicall',
        input_value={
            'command': command,
            'secret':setting.get('secret'),
            'compute_endpoint': compute_endpoint,
        }
    ).get('output_value').get('result')    
    count = result.get("listvirtualmachinesresponse").get("count")

    # return the count of the running VMs
    return this.success(f'VMs running: {count}')
