import uuid
import textwrap
import time


def handler(system, this):
    now = time.time()
    env_name = system.get_env_name()
    check_id = uuid.uuid4().hex
    client_name, user_name = this.get('client_name', 'user_name')
    this.log(now=now, check_id=check_id, client_name=client_name, user_name=user_name)
    report = {
        'now': now,
        'check_id': check_id,
        'client_name': client_name,
        'user_name': user_name,
    }

    # start a script execution via the rest api
    script = textwrap.dedent('''
        def handler(system, this):
            return this.error('done')
        ''')
    check_task = this.task(
        'REST',
        url=f'https://{env_name}.cloudomation.io/api/1/execution',
        method='POST',
        json={
            'script': script,
            'name': 'availability.check.script',
        },
        pass_user_token=True,
        name='availability.check.task',
        run=True,
        wait=system.return_when.ALL_ENDED,
    )
    check_task_status, check_task_message = check_task.load('status', 'message')
    this.log(check_task=(check_task_status, check_task_message))
    report.update({
        'check_task': (check_task_status, check_task_message),
    })
    if check_task_status != 'success':
        system.setting('availability.check.history').list_append(report)
        return this.error(f'task did not succeed: {check_task_message}')
    check_script_id = check_task.get('output_value')['json']['id']
    check_script = system.execution(check_script_id)
    check_script.wait(return_when=system.return_when.ALL_ENDED)
    check_script_status, check_script_message = check_script.load('status', 'message')
    this.log(check_script=(check_script_status, check_script_message))
    report.update({
        'check_script': (check_script_status, check_script_message),
    })
    if check_script_status != 'success':
        system.setting('availability.check.history').list_append(report)
        return this.error(f'script did not succeed: {check_script_message}')
    # task & script succeeded
    this.save(retention_time=1)
    check_task.save(expires=now+60)
    check_script.save(expires=now+60)
    return this.success('all done')
