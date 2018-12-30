def handler(system, this):
    # get AWS credentials from setting
    credentials = system.setting('aws credentials').get('value')
    # create a child execution task which talks with AWS
    task = this.task(
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
        **credentials
    ).run()  # run the task
    # provide the response back to the caller
    this.log(task.get('output_value'))
    this.success('all done')
