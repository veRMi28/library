def handler(system, this):
    # Authenticate using private key
    info_task = this.task(
        'SSH',
        # public accessible name or IP
        hostname='my-ssh-server',
        # key to check host identity.
        # can be read with "$ ssh-keyscan -t rsa <my-ssh-server>"
        hostkey='ssh-rsa AAAAB3NzaC1yc2E...',
        username='kevin',
        key='-----BEGIN RSA PRIVATE KEY-----\nMII...',
        script=(
            '''
            HOSTNAME=$(hostname)
            USERNAME=$(id -un)
            CPU=$(uname -p)
            #OUTPUT_VAR(HOSTNAME)
            #OUTPUT_VAR(USERNAME)
            #OUTPUT_VAR(CPU)
            '''
        ),
    )

    outputs = info_task.get('output_value')
    hostname = outputs['var']['HOSTNAME']
    username = outputs['var']['USERNAME']
    cpu = outputs['var']['CPU']

    this.log(f'info_task was running on {hostname} using {cpu} as {username}')

    # Authenticate using password
    uptime_task = this.task(
        'SSH',
        hostname='my-ssh-server',
        hostkey='ssh-rsa AAAAB3NzaC1yc2E...',
        username='kevin',
        password='***',
        script=(
            '''
            UPTIME=$(uptime -s)
            #OUTPUT_VAR(UPTIME)
            '''
        ),
    )

    outputs = uptime_task.get('output_value')
    uptime = outputs['var']['UPTIME']

    this.log(f'{hostname} is up since {uptime}')

    return this.success('all done')
