import re


def handler(c):
    # Authenticate using private key
    info_task = c.task(
        'SSH',
        # public accessible name or IP
        hostname='my-ssh-server',
        # key to check host identiy.
        # can be read with "$ ssh-keyscan -t rsa <my-ssh-server>"
        hostkey='ssh-rsa AAAAB3NzaC1yc2E...',
        username='kevin',
        key='-----BEGIN RSA PRIVATE KEY-----\nMII...',
        script='''
               echo "hostname" "'$(hostname)'"
               echo "username" "'$(id -un)'"
               echo "cpu" "'$(uname -p)'"
               '''
    ).run()

    report = info_task.get_outputs()['report']
    hostname = re.search("hostname '([^']*)'", report).group(1)
    username = re.search("username '([^']*)'", report).group(1)
    cpu = re.search("cpu '([^']*)'", report).group(1)

    c.logln(f'info_task was running on {hostname} using {cpu} as {username}')

    # Authenticate using password
    uptime_task = c.task(
        'SSH',
        hostname='my-ssh-server',
        hostkey='ssh-rsa AAAAB3NzaC1yc2E...',
        username='kevin',
        password='***',
        script='''
               echo "up since" "'$(uptime -s)'"
               '''
    ).run()

    report = uptime_task.get_outputs()['report']
    up_since = re.search("up since '([^']*)'", report).group(1)

    c.logln(f'{hostname} is up since {up_since}')
