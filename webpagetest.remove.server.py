import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    inputs = this.get('input_value')
    gcloud_connection = inputs.get('gcloud_connection')
    project_id = system.connection(gcloud_connection).get('value').get('key').get('project_id')
    if project_id is None or gcloud_connection is None:
        return this.error('Missing inputs')

    delete_task = this.connect(
        gcloud_connection,
        name='delete webpagetest-server',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='delete',
        params={
            'instance': 'webpagetest-server',
            'project': project_id,
            'zone': 'europe-west1-b',
        },
        wait=system.return_when.ALL_ENDED,
    )
    status = delete_task.get('status')
    message = delete_task.get('message')
    operation = delete_task.get('output_value').get('result')
    this.flow(
        'google_operation_wait',
        operation=operation,
    )
    
    system.setting('webpagetestserver').release()

    if status == 'ENDED_ERROR' and 'HttpError 404' not in message:
        return this.error('failed to delete webpagetest-server')

    webpagetestserver = system.setting('webpagetestserver').get('value')
    webpagetestserver['active'] = False
    system.setting('webpagetestserver').save(value=webpagetestserver)

    return this.success('all done')
