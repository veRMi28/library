import textwrap


def handler(system, this):
    # ======= configuration =======

    # Required: store AWS credentials in a setting
    # The setting should contain two keys:
    # 'aws_access_key_id' and 'aws_secret_access_key'
    credentials_setting = 'aws.credentials'

    # Required: a name which is used as a prefix for all AWS resources which
    # are created in this example
    name = 'Cloudomation-aws-example'

    # Optional: The ID of the VPC to use. If you do not supply a VPC ID, the
    # default VPC will be used
    vpc_id = None

    # Optional: The ID of the security group which will be applied to the
    # new instance. For this example to work, the security should should
    # allow incoming SSH connections on port 22. If you do not supply a
    # security_group_id a new security should will be created.
    security_group_id = None

    # Optional: Choose if you want the flow script to pause before cleaning up
    interactive_cleanup = False

    # ======= end of configuration =======

    # get AWS credentials from setting
    credentials = system.setting(credentials_setting).get('value')

    # create a template task we can re-use for different calls
    aws_template = this.task(
        'AWS',
        region='eu-central-1',
        init={
            'protect_inputs': [
                'aws_access_key_id',
                'aws_secret_access_key',
            ],
        },
        **credentials,
        save=False,
    )

    # run everything in a try statement,
    # so we can clean up if anything goes wrong
    instance_id = None
    key_name = f'{name}-key'
    clean_security_group = False
    describe_vpcs = None
    try:

        if not vpc_id:
            # asyncrounously find default VPC
            describe_vpcs = aws_template.clone(
                name='find default vpc id',
                client='ec2',
                service='describe_vpcs',
                parameters={
                    'Filters': [{
                        'Name': 'isDefault',
                        'Values': ['true'],
                    }],
                },
                run=True,
                wait=False,
            )

        # asyncrounously find latest amazon linux image_id
        get_parameters = aws_template.clone(
            name='read image id',
            client='ssm',
            service='get_parameters',
            parameters={
                'Names': [
                    '/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2'
                ],
            },
            run=True,
            wait=False,
        )

        # asyncrounously create a new key pair
        create_key_pair = aws_template.clone(
            name='create new key pair',
            client='ec2',
            service='create_key_pair',
            parameters={
                'KeyName': key_name,
            },
            init={
                'protect_outputs': [
                    'result',
                ],
            },
            run=True,
            wait=False,
        )

        if not security_group_id:
            if not vpc_id:
                # wait for describe_vpcs to end
                this.wait_for(describe_vpcs)
                describe_vpcs_outputs = describe_vpcs.get('output_value')
                vpc_id = describe_vpcs_outputs['result']['Vpcs'][0]['VpcId']
                this.log(vpc_id=vpc_id)

            # create a security group
            create_security_group_outputs = aws_template.clone(
                name='create security group',
                client='ec2',
                service='create_security_group',
                parameters={
                    'Description': 'Allow SSH for Cloudomation example',
                    'GroupName': f'{name}-security-group',
                    'VpcId': vpc_id,
                },
                run=True,
            ).get('output_value')
            security_group_id = create_security_group_outputs['result']['GroupId']
            this.log(security_group_id=security_group_id)
            clean_security_group = True

            # authorize incoming SSH traffic on port 22
            aws_template.clone(
                name='authorize SSH traffic',
                client='ec2',
                service='authorize_security_group_ingress',
                parameters={
                    'CidrIp': '0.0.0.0/0',
                    'FromPort': 22,
                    'ToPort': 22,
                    'GroupId': security_group_id,
                    'IpProtocol': 'tcp',
                },
                run=True,
            )

        # wait for both, get_parameters and create_key_pair tasks to end
        this.wait_for(get_parameters, create_key_pair)

        get_parameters_outputs = get_parameters.get('output_value')
        image_id = get_parameters_outputs['result']['Parameters'][0]['Value']
        this.log(image_id=image_id)

        create_key_pair_outputs = create_key_pair.get('output_value')
        key_name = create_key_pair_outputs['result']['KeyName']
        private_key = create_key_pair_outputs['result']['KeyMaterial']
        this.log(key_name=key_name)

        # launch an EC2 instance
        run_instance_outputs = aws_template.clone(
            name='run instance',
            client='ec2',
            service='run_instances',
            parameters={
                'ImageId': image_id,
                'InstanceType': 't2.micro',
                'MaxCount': 1,
                'MinCount': 1,
                'KeyName': key_name,
                'SecurityGroupIds': [security_group_id],
            },
            run=True,
        ).get('output_value')
        instance_id = run_instance_outputs['result']['Instances'][0]['InstanceId']
        this.log(instance_id=instance_id)

        # wait until the instance is running
        aws_template.clone(
            name='wait for instance running',
            client='ec2',
            waiter='instance_running',
            parameters={
                'InstanceIds': [
                    instance_id,
                ]
            },
            run=True,
        )

        # read public IP of instance
        describe_instances_outputs = aws_template.clone(
            name='describe instance',
            client='ec2',
            service='describe_instances',
            parameters={
                'InstanceIds': [
                    instance_id,
                ]
            },
            run=True,
        ).get('output_value')
        public_ip = describe_instances_outputs['result']['Reservations'][0]['Instances'][0]['PublicIpAddress']
        this.log(public_ip=public_ip)

        # read console output to find host key
        # the call might return without an actual output, we have to loop until we receive an actual output
        get_console_output = None
        while True:
            if get_console_output:
                get_console_output.delete()
            get_console_output = aws_template.clone(
                name='get console output',
                client='ec2',
                service='get_console_output',
                parameters={
                    'InstanceId': instance_id,
                },
                run=True,
            )
            get_console_output_outputs = get_console_output.get('output_value')
            console = get_console_output_outputs['result'].get('Output')
            if console:
                in_hostkeys = False
                hostkey = None
                for line in console.splitlines():
                    if line.strip() == '-----BEGIN SSH HOST KEY KEYS-----':
                        in_hostkeys = True
                    elif line.strip() == '-----END SSH HOST KEY KEYS-----':
                        in_hostkeys = False
                    elif in_hostkeys:
                        if line.startswith('ssh-rsa '):
                            hostkey = line.strip()
                            break
                if hostkey:
                    this.log(hostkey=hostkey)
                    break
            # wait 30 seconds before requesting console output again
            this.sleep(30)

        # connect to the instance
        this.task(
            'SSH',
            name='connect to host',
            hostname=public_ip,
            hostkey=hostkey,
            username='ec2-user',
            key=private_key,
            script=textwrap.dedent(
                '''
                id
                uname -a
                '''
            ),
            run=True,
        )

    # clean up
    finally:
        if interactive_cleanup:
            this.save(message='waiting before cleanup')
            this.pause()
        this.save(message='cleaning up')

        if instance_id:
            # remove instance
            aws_template.clone(
                name='terminate instance',
                client='ec2',
                service='terminate_instances',
                parameters={
                    'InstanceIds': [instance_id],
                },
                run=True,
            )
            # wait for instance to be terminated
            aws_template.clone(
                name='wait for instance terminated',
                client='ec2',
                waiter='instance_terminated',
                parameters={
                    'InstanceIds': [instance_id],
                },
                run=True,
            )

        if key_name:
            # remove key pair
            aws_template.clone(
                name='delete key pair',
                client='ec2',
                service='delete_key_pair',
                parameters={
                    'KeyName': key_name,
                },
                run=True,
            )

        if clean_security_group and security_group_id:
            # remove security group
            aws_template.clone(
                name='delete security group',
                client='ec2',
                service='delete_security_group',
                parameters={
                    'GroupId': security_group_id,
                },
                run=True,
            )

    return this.success('all done')
