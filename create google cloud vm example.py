import json
import datetime
from Crypto.PublicKey import RSA

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    """ 
        In this example we setup a Virtual Machine (VM) in the google-cloud. 
        Then, Ubuntu will be installed and a small bash script is executed. 
        Bash scripts can be used to install more software on the VM or 
        change settings, anything you could do on a local machine in a terminal.  

        This flow also requires the two files:
        * create google cloud vm example.sh
        * create google cloud vm example.json
        In the future, you can take these as an example, adopt them and 
        upload them with a new name in Cloudomation > Files.
    """

    # This is a pop-up message form, it will ask for some information 
    # The last element is an OK-button, after clicking it the 
    # values are passed further and the pop-up message closes.
    form_response = system.message(
        subject='Input information to setup a VM in google-cloud',
        message_type = 'POPUP',
        body={
            'type': 'object',
            'properties': {
                'connection_name': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter name for the connection: \n\
(This name can be searched for and is used to connect with your VM)',
                    'example': 'my-vm-on-gcloud',
                    'order': 1,
                },
                'project_id': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter your google cloud project-ID:',
                    'default': 'my-first-project-id',
                    'order': 2,
                },
                'machine_type': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the machine type you want to use on google-cloud:',
                    'default': 'n1-standard-1',
                    'order': 3,
                },
                'server_location': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the desired location of the hosting server from google-cloud:',
                    'default': 'europe-west1-b',
                    'order': 4,
                },
                'Ok': {
                    'element': 'submit',
                    'label': 'OK',
                    'type': 'boolean',
                    'order': 5,
                },
            },
            'required': [
                'connection_name',
                'project_id',
                'machine_type',
                'server_location',
            ],
        },
    ).wait().get('response')
    connection_name = form_response['connection_name']
    project_id = form_response['project_id']
    machine_type = form_response['machine_type']
    server_location = form_response['server_location']

    # generate a ssh key-pair for the setup-user:
    setup_user_key = RSA.generate(2048)
    setup_user_priv = setup_user_key.export_key().decode()
    setup_user_pub = setup_user_key.publickey().export_key(format='OpenSSH').decode()
    setup_user_key = None

    # load the startup script and pass the public ssh key to the script: 
    vm_startup_script = system.file(
        'create google cloud vm example.sh').get('content')
    vm_startup_script = vm_startup_script.format(
        setup_user_pub=setup_user_pub,
    )

    # load the configuration for the VM and setup last parameters:
    vm_config_str = system.file(
        'create google cloud vm example.json').get('content')
    vm_config = json.loads(vm_config_str)
    vm_config['name'] = connection_name
    vm_config['machineType'] = \
        f'projects/{project_id}/zones/{server_location}/machineTypes/{machine_type}'
    vm_config['zone'] = f'projects/{project_id}/zones/{server_location}'
    vm_config['metadata']['items'][0]['value'] = vm_startup_script
    vm_config['disks'][0]['deviceName'] = connection_name
    vm_config['disks'][0]['initializeParams']['diskType'] = \
        f'projects/{project_id}/zones/{server_location}/diskTypes/pd-ssd'
    vm_config['networkInterfaces'][0]['subnetwork'] = \
        f'projects/{project_id}/regions/{server_location[:-2]}/subnetworks/default'
    # NOTE: two sources can be used for initial system installation:
    # a) from 'sourceSnapshot'
    # b) from 'sourceImage'
    # This flow script will install Ubuntu, using the parameter 'sourceImage'.
    # For installing a system from snapshot use the respective parameter.
    # This paramter is set under: disks / initializeParams
        
    # Connect to the VM
    operation = this.connect(
        'gcloud',
        name=f'launch {connection_name}',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='insert',
        params={
            'project': project_id,
            'zone': server_location,
            'body': vm_config,
        },
    ).get('output_value')['result']
    this.flow(
        'google_operation_wait',
        operation=operation,
    )

    # retrieve external IP and hostkey (required for creating a SSH connection):
    for _ in range(60):
        try:
            instance_list = this.connect(
                'gcloud',
                name=f'find {connection_name}',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='list',
                params={
                    'project': project_id,
                    'zone': server_location,
                    'filter': f'name={connection_name}',
                },
            ).get('output_value')
        except flow_api.DependencyFailedError:
            this.sleep(1)
        if len(instance_list['result'].get('items', [])) != 0:
            break
        this.sleep(1)
    else:
        return this.error('did not find VM within 60 tries')
    external_ip = instance_list['result']['items'][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

    last_try_guest_attribute = None
    for _ in range(60):
        if last_try_guest_attribute is not None:
            last_try_guest_attribute.archive()
        try:
            last_try_guest_attribute = this.connect(
                'gcloud',
                name=f'get {connection_name} hostkey',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='getGuestAttributes',
                params={
                    'project': project_id,
                    'zone': server_location,
                    'instance': connection_name,
                    'queryPath': 'hostkeys/ssh-rsa',
                },
                wait=system.return_when.ALL_ENDED,
            )
        except Exception:
            this.sleep(1)
        else:
            if last_try_guest_attribute.load('status') == 'ENDED_SUCCESS':
                break
    else:
        return this.error('did not find hostkey within 60 tries')
    hostkey = last_try_guest_attribute.get('output_value')['result']['queryValue']['items'][0]['value']

    # setup the SSH connection for the VM
    system.connection(f'{connection_name}-ssh').save(
        connection_type='SSH',
        value={
            'hostname': external_ip,
            'hostkey': hostkey,
            'username': 'setup-user',
            'key': setup_user_priv,
            'script_timeout': 600,
            'interpreter': '/usr/bin/env bash -ex',
        },
    )

    # Run a little bash script on the VM:
    last_try_script_echo = None
    for _ in range(20):
        if last_try_script_echo is not None:
            last_try_script_echo.archive()
        try:
            last_try_script_echo = this.connect(
                f'{connection_name}-ssh',
                script="""
                    echo "litte test content" >> ~/test_file.txt
                    cat ~/test_file.txt
                    rm ~/test_file.txt
                    """,
                name='run test script on new vm',
            )
        except:
            this.sleep(1)
        else:
            if last_try_script_echo.load('status') == 'ENDED_SUCCESS':
                break
    else:
        return this.error('Failed to run the little test script.')
    script_echo = last_try_script_echo.get('output_value')['report']
    this.set_output(f'Echo from test-script:\n{script_echo}')

    # Save flow state and pause, manually resume this script's execution to remove the VM
    this.save(message='The VM was successfully deployed. Resume this execution to remove the VM')
    this.pause()

    # Remove the VM
    operation = this.connect(
        'gcloud',
        name=f'remove {connection_name}',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='delete',
        params={
            'project': project_id,
            'zone': server_location,
            'instance': connection_name,
        },
    ).get('output_value')['result']
    this.flow(
        'google_operation_wait',
        operation=operation,
    )

    return this.success('all done')
