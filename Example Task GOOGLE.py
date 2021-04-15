import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    this.task(
        'GOOGLE',
        name='launch instance',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='insert',
        kwargs={
            'body': instance_config,
            'project': project_id,
            'zone': 'europe-west3-b',
        }
        key=key,
        scopes=['https://www.googleapis.com/auth/compute'],
    )
    this.log('instance was started')

    return this.success('all done')
