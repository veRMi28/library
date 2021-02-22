import json
import datetime
from Crypto.PublicKey import RSA

import flow_api


def handler(system, this):
    """ 
        In this example we setup a Virtual Machine (VM) in the google-cloud. 
        Then, Ubuntu will be installed and a small bash script is executed. 
        Bash scripts can be used to install more software on the VM or 
        change settings, anything you could do on a local machine in a terminal.  

        This flow also requires the two files:
        * create vm from snapshot example.sh
        * create vm from snapshot example.json
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
                'project_name': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the name of your project on google-cloud:',
                    'default': 'my-first-project-id',
                    'order': 2,
                },
                'machine_type': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the machine type you want to use on google-cloud:',
                    'default': 'n1-highcpu-4',
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
                'project_name',
                'machine_type',
                'server_location',
            ],
        },
    ).wait().get('response')
    connection_name = form_response['connection_name']
    project_id = form_response['project_name']
    machine_type = form_response['machine_type']
    server_location = form_response['server_location']

    # generate a ssh key-pair for the setup-user:
    setup_user_key = RSA.generate(2048)
    setup_user_priv = setup_user_key.export_key().decode()
    setup_user_pub = setup_user_key.publickey().export_key(format='OpenSSH').decode()
    setup_user_key = None

    # load the startup script and pass the public ssh key to the script: 
    vm_startup_script = system.file(
        'create vm from snapshot example.sh').get('content')
    vm_startup_script = vm_startup_script.format(
        setup_user_pub=setup_user_pub,
    )

    # load the configuration for the VM and setup last parameters:
    vm_config_str = system.file(
        'create vm from snapshot example.json').get('content')
    vm_config = json.loads(vm_config_str)
    vm_config['name'] = f'{connection_name}'
    vm_config['machineType'] = \
        f'projects/{project_id}/zones/{server_location}/machineTypes/{machine_type}'
    vm_config['zone'] = f'projects/{project_id}/zones/{server_location}'
    vm_config['metadata']['items'][0]['value'] = vm_startup_script
    vm_config['disks'][0]['deviceName'] = f'{connection_name}'
    vm_config['disks'][0]['diskType'] = \
        f'projects/{project_id}/zones/{server_location}/diskTypes/pd-ssd'
    vm_config['networkInterfaces'][0]['subnetwork'] = \
        f'projects/{project_id}/regions/europe-west1/subnetworks/default'
    # NOTE: two sources can be used for initial system installation:
    # a) from 'sourceSnapshot'
    # b) from 'sourceImage'
    # In the example .json the parameter 'sourceSnapshot' is defined. 
    # This flow script shall install Ubuntu which is provided from a 'sourceImage'.
    # Since only either of the two options can be given as a parameter, 
    # the paramter 'sourceSnapshot' must be removed 
    # (either here, see below, or in the .json).
    find_image_name = this.flow('find build-server image name', wait=False)
    image_name = find_image_name.wait().get('output_value')['image_name']
    vm_config['disks'][0]['initializeParams'][
        'sourceImage'] = f'projects/ubuntu-os-cloud/global/images/{image_name}'
    try:
        del vm_config['disks'][0]['initializeParams']['sourceSnapshot']
    except KeyError:
        pass
        
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

    try:
        # retrieve external IP and hostkey (required for creating a SSH connection):
        for _ in range(60):
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
            if len(instance_list['result'].get('items', [])) != 0:
                break
            this.sleep(1)
        else:
            return this.error('did not find VM within 60 tries')
        external_ip = instance_list['result']['items'][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

        failed_tries = []
        for _ in range(60):
            this.sleep(1)
            guest_attribute_task = this.connect(
                'gcloud',
                name=f'get {connection_name} hostkey',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='getGuestAttributes',
                params={
                    'project': project_id,
                    'zone': server_location,
                    'instance': f'{connection_name}',
                    'queryPath': 'hostkeys/ssh-rsa',
                },
                wait=system.return_when.ALL_ENDED,
            )
            if guest_attribute_task.load('status') == 'ENDED_SUCCESS':
                break
            failed_tries.append(guest_attribute_task)
        else:
            return this.error('did not find hostkey within 60 tries')
        for failed_try in failed_tries:
            failed_try.archive()
        hostkey = guest_attribute_task.get('output_value')[
            'result']['queryValue']['items'][0]['value']

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
        this.sleep(15)

        # Run a little bash script on the VM:
        script_echo = dict(result='')
        try:
            script_echo = this.connect(
                f'{connection_name}-ssh',
                script="""
                    echo "litte test content" >> ~/test_file.txt
                    cat ~/test_file.txt
                    rm ~/test_file.txt
                    """,
                name='run test script on new vm',
            ).get('output_value')['report']
        except Exception as err:
            return this.error(f'Failed to run the little test script. \n{repr(err)}')
        else:
            # this.set_output(f'Echo from test-script:\n{script_echo['result']}')
            this.set_output(f'Echo from test-script:\n{script_echo}')

        # Example: Stop the VM
        operation = this.connect(
            'gcloud',
            name=f'stop {connection_name}',
            api_name='compute',
            api_version='v1',
            collection='instances',
            request='stop',
            params={
                'project': project_id,
                'zone': server_location,
                'instance': f'{connection_name}',
            },
        ).get('output_value')['result']
        this.flow(
            'google_operation_wait',
            operation=operation,
        )

    except Exception as ex:
        this.save(message=repr(ex))
        raise
    finally:
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
        this.set_output(f'Found instances of this VM:\n{instance_list}')
    return this.success('all done')
