def handler(c):
    # get AWS credentials from setting
    creds = c.setting('aws creds')
    # create a child execution task which talks with AWS
    task = c.task(
        'AWS',
        region='eu-central-1',
        client='ec2',
        service='run_instances',
        parameters={
            'ImageId': 'ami-0f5dbc86dd9cbf7a8',
            'InstanceType': 't2.micro',
            'MaxCount': 1,
            'MinCount': 1,
        },
        **creds
    ).run()  # run the task
    # provide the response back to the caller
    c.set_output('task out', task.get_outputs())
    c.end('success', message='all done')
