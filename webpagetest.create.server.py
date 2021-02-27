import json
from datetime import datetime

import flow_api

'''
Creates and starts a server from a template called webpagetest-server-template
Inputs:
    gcloud_connection: <string> name of the connection stored in the cloudomation workspace
Outputs:
    wait: <bool> False, if the server is already running, otherwise True
'''

def handler(system: flow_api.System, this: flow_api.Execution):
    inputs = system.get('input_value')
    gcloud_connection = inputs.get('gcloud_connection')
    project_id = system.connection(gcloud_connection).get('value').get('key').get('project_id')
    if project_id is None or gcloud_connection is None:
        return this.error('Missing inputs')

    try:
        webpagetestserver = system.setting('webpagetestserver').get('value')
        if webpagetestserver.get('active'):
            this.set_output(wait=False)
            return this.success('Server already active')
    except:
        webpagetestserver = system.setting('webpagetestserver')

    this.save(message=f'waiting for webpagetestserver lock')
    system.setting('webpagetestserver').acquire(timeout=None)
    this.save(message=f'creating webpagetest server')

    webpagetest_server_config_str = system.file('webpagetest-server.json').get('content')
    webpagetest_server_config = json.loads(webpagetest_server_config_str)
    webpagetest_server_config['name'] = 'webpagetest-server'
    webpagetest_server_config['disks'][0]['deviceName'] = 'webpagetest-server'
    webpagetest_server_config['disks'][0]['initializeParams']['sourceSnapshot'] = f'projects/{project_id}/global/snapshots/webpagetest-server-template'

    launch_task = this.connect(
        gcloud_connection,
        name='launch webpagetest-server',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='insert',
        params={
            'body': webpagetest_server_config,
            'project': project_id,
            'zone': 'europe-west1-b',
        },
        wait=system.return_when.ALL_ENDED,
    )
    status = launch_task.get('status')
    message = launch_task.get('message')
    if status == 'ENDED_ERROR' and 'HttpError 409' in message:
        return this.success('using existing webpagetestserver')
    if status == 'ENDED_ERROR':
        return this.error('failed to launch webpagetest-server')
    
    operation = launch_task.get('output_value')['result']

    this.flow(
        'google_operation_wait',
        operation=operation,
    )

    for _ in range(60):
        instance_list = this.connect(
            gcloud_connection,
            name='find webpagetest-server',
            api_name='compute',
            api_version='v1',
            collection='instances',
            request='list',
            params={
                'filter': 'name=webpagetest-server',
                'project': project_id,
                'zone': 'europe-west1-b',
            },
        ).get('output_value')
        if len(instance_list['result'].get('items', [])) != 0:
            break
        this.sleep(1)
    else:
        return this.error('did not find webpagetest server within 60 tries')
    external_ip = instance_list['result']['items'][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

    webpagetestserver = system.setting('webpagetestserver').get('value')
    if webpagetestserver is None:
        webpagetestserver = {}
    webpagetestserver['hostname'] = external_ip
    webpagetestserver['created_at'] = datetime.timestamp(datetime.now())
    webpagetestserver['active'] = True
    system.setting('webpagetestserver').save(value=webpagetestserver)
    this.set_output(wait=True)  # wait until the docker containers are ready

    return this.success('all done')