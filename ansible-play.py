def handler(system, this):
    """
    Execute an ansible playbook


    Copy a playbook to an ansible host and execute it. This flow script is
    meant to be a boilerplate and should be adjusted to your needs.


    Parameters:
        ansible-host: the name of the setting which contains the connection
            information for the ansible master host. Here's a template:
            ```yaml
            hostname: TODO
            hostkey: ssh-rsa TODO
            username: TODO
            key: |
              -----BEGIN RSA PRIVATE KEY-----
              TODO
              -----END RSA PRIVATE KEY-----
            ```
        playbook: The path & name of the ansible playbook yaml file
        become: If true, execute the playbook as root
        files: A list of files which will be copied to the ansible host to
            be used by the playbook


    Returns:
        The report of the ansible-playbook invocation
    """
    inputs = this.get('input_value')
    ansible_host_setting = inputs.get('ansible-host', 'ansible-host')
    target_hosts = inputs.get('target')
    files = inputs.get('files', [])
    playbook = inputs['playbook']
    script = f'ansible-playbook {playbook}'
    become = inputs.get('become')
    if become:
        script += ' -b'
    if target_hosts:
        script += f' -i "{target_hosts},"'
    ansible_host = system.setting(ansible_host_setting).get('value')
    tasks = []
    for file in files:
        tasks.append(this.task(
            'SCP',
            **ansible_host,
            src=f'cloudomation:ansible-integration-demo/{file}',
            dst=file,
            run=True,
            wait=False,
        ))
    tasks.append(this.task(
        'SCP',
        **ansible_host,
        src=f'cloudomation:ansible-integration-demo/{playbook}',
        dst=playbook,
        run=True,
        wait=False,
    ))
    this.wait_for(*tasks)
    report = this.task(
        'SSH',
        **ansible_host,
        script=script,
        run=True,
    ).get('output_value')['report']
    this.save(output_value={'report': report})
    return this.success('all done')
