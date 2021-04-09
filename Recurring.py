import time
from datetime import datetime, timezone

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    inputs = this.get('input_value') or {}
    message_id = inputs.get('message_id')

    if message_id is None:
        defaults = {
            'interval': 60,
            'wait': True,
        }
        if 'flow_name' in inputs:
            defaults['flow_name'] = inputs['flow_name']
        if 'flow_id' in inputs:
            defaults['flow_name'] = system.flow(inputs['flow_id'], by='id').get('name')

        message = system.message(
            subject='Recurring execution',
            body={
                'type': 'object',
                'properties': {
                    'flow_name': {
                        'label': 'Name of the flow which should be started recurring',
                        'element': 'string',
                        'type': 'string',
                        'example': defaults.get('flow_name'),
                        'default': defaults.get('flow_name'),
                        'order': 1,
                    },
                    'interval': {
                        'label': 'Interval of recurring execution in seconds',
                        'element': 'number',
                        'type': 'number',
                        'example': defaults['interval'],
                        'default': defaults['interval'],
                        'order': 2,
                    },
                    'wait': {
                        'label': 'Wait for child executions to finish',
                        'element': 'toggle',
                        'type': 'boolean',
                        'default': defaults['wait'],
                        'order': 3,
                    },
                    'max_iterations': {
                        'label': 'Maximum number of iterations (unlimited if omitted)',
                        'element': 'number',
                        'type': 'number',
                        'order': 4,
                    },
                    'start': {
                        'label': 'Start recurring',
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 5,
                    },
                },
                'required': [
                    'flow_name',
                    'interval',
                ],
            },
        )
        message_id = message.get('id')
        this.save(output_value={
            'message_id': message_id,
        })
        this.flow(
            'Recurring',
            name='Recurring execution',
            message_id=message_id,
            wait=False,
        )
        return this.success('requested details')

    message = system.message(message_id)
    response = message.wait().get('response')
    this.log(response=response)
    flow_name = response['flow_name']
    interval = response['interval']
    wait = response['wait']
    max_iterations = response.get('max_iterations')
    this.save(name=f'Recurring {flow_name}')

    # Loop
    iterations = 0
    start = time.time()
    while max_iterations is None or iterations < max_iterations:
        iterations += 1
        if max_iterations:
            this.save(message=f'iteration {iterations}/{max_iterations}')
        else:
            this.save(message=f'iteration {iterations}')
        # Start child execution
        inputs = {
            'start': start,
            'iterations': iterations,
            'max_iterations': max_iterations,
        }
        child = this.flow(
            flow_name,
            inputs=inputs,
            name=f'{flow_name} iteration #{iterations}',
            run=False
        )
        if wait:
            try:
                child.run()
            except Exception:
                this.log(f'iteration #{iterations} failed')
        else:
            child.run_async()
        if max_iterations is not None and iterations >= max_iterations:
            break
        if wait:
            now = time.time()
            scheduled = datetime.fromtimestamp(now + interval, timezone.utc)
        else:
            scheduled = datetime.fromtimestamp(start + (iterations * interval), timezone.utc)
        scheduled_ts = scheduled.isoformat(sep=' ', timespec='minutes')
        this.save(message=scheduled_ts)
        if wait:
            this.sleep(interval)
        else:
            this.sleep_until(start + (iterations * interval))

    return this.success(f'started {iterations} iterations')
