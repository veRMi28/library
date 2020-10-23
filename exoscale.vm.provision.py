import time

"""
Setup and start a VM

This example requires a setting with name 'exoscale.api' which contains:
key: your-api-key
secret: your-api-secret

If the machine does not start within 1 minute, the script returns an error message.

inputs:
    - service_name:
        type: string
        required: False
        default: Micro
        doc: the name of the service (cpu/ram/ssd size of the machine)
    - template_name:
        type: string
        required: False
        default: Ubuntu 19.10
        doc: the name of the template (which operating system, software etc.)
    - zone_name:
        type: string
        required: False
        default: at-vie-1
        doc: where to spin up the virtual machine

"""

def handler(system, this):
    
    # retrieve the apikey and secret from the system setting
    setting = system.setting('exoscale.api').get('value')

    # default values for inputs
    service_name = 'Micro'
    template_name = 'Ubuntu 19.10'
    zone_name = 'at-vie-1'
    compute_endpoint = 'https://api.exoscale.ch/compute'

    # check if we got inputs
    inputs = this.get('input_value')
    if inputs.get('service_name'):
        service_name = inputs.get('service_name')
    if inputs.get('template_name'):
        template_name = inputs.get('template_name')
    if inputs.get('zone_name'):
        zone_name = inputs.get('zone_name')    
    
    # retrieve the available services
    command = {
        'command': 'listServiceOfferings',
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

    # check if the service we want is among the available 
    # services and get the id of the service
    service_offering_id = None    
    for so in result.get('listserviceofferingsresponse').get('serviceoffering'):
        if so.get('name') == service_name:
            service_offering_id = so.get('id')
            break
    if not service_offering_id:
        return this.error(f'could not find service name: {service_name}')
    
    # retrieve the available templates
    command = {
        'command': 'listTemplates',
        'templatefilter': 'featured',
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

    # check if the template we want is among the available
    # templates and get the id of the template
    template_id = None
    for t in result.get('listtemplatesresponse').get('template'):
        if template_name in t.get('name'):
            template_id = t.get('id')
            break
    if not template_id:
        return this.error(f'could not find template name: {template_name}')
    
    # retrieve the available zones
    command = {
        'command': 'listZones',
        'available': 'true',
        'apikey': setting.get('key'),
    }
    result = this.flow(
        'acs.apicall',
        input_value={
            'command':command,
            'secret': setting.get('secret'),
            'compute_endpoint': compute_endpoint,
        },
    ).get('output_value').get('result')

    # check if the zone we want is among the available 
    # zones and get the id of the zone
    zone_id = None
    for z in result.get('listzonesresponse').get('zone'):
        if z.get('name') == zone_name:
            zone_id = z.get('id')
            break
    if not zone_id:
        return this.error(f'could not find zone name: {zone_name}')
    
    # deploy the VM with the collected ids
    command = {
      'command': 'deployVirtualMachine',
      'serviceofferingid': service_offering_id,
      'templateid': template_id,
      'zoneid': zone_id,
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
    
    # with the jobid we can query the status of the deployment
    jobid = result.get('deployvirtualmachineresponse').get('jobid')        
    if not jobid:
        return this.error('could not create VM - no jobid')
    
    # check if the VM is running after 60 seconds
    time.sleep(60)
    instance_name = None
    command = {
        'command': 'queryAsyncJobResult',
        'jobid': jobid,
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
    
    # return success if the VM is running
    vm = result.get('queryasyncjobresultresponse',{}).get('jobresult',{}).get('virtualmachine',{})
    if vm.get('state') == 'Running':
        instance_name = vm.get('displayname')
        return this.success(f'VM {instance_name} is up and running.')
    
    return this.error('Instance did not start in time')