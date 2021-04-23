import datetime, pytz
import flow_api

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    inputs = this.get('input_value') or {}
    message_id = inputs.get('message_id')

    if message_id is None:
        defaults = {
            'scheduled_at': '08:30',
        }
        if 'flow_name' in inputs:
            defaults['flow_name'] = inputs['flow_name']
        if 'flow_id' in inputs:
            defaults['flow_name'] = system.flow(inputs['flow_id'], by='id').get('name')
        message = system.message(
            subject='Scheduled execution',
            body={
                'type': 'object',
                'properties': {
                    'flow_name': {
                        'label': 'Name of the flow which should be scheduled',
                        'element': 'string',
                        'type': 'string',
                        'example': defaults.get('flow_name'),
                        'default': defaults.get('flow_name'),
                        'order': 1,
                    },
                    'scheduled_at': {
                        'label': 'Time when the child execution should be started',
                        'element': 'time',
                        'type': 'string',
                        'format': 'time',
                        'default': defaults['scheduled_at'],
                        'order': 2,
                    },
                    'max_iterations': {
                        'label': 'Maximum number of iterations (unlimited if omitted)',
                        'element': 'number',
                        'type': 'number',
                        'order': 3,
                    },
                    'start': {
                        'label': 'Start schedule',
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 4,
                    },
                },
                'required': [
                    'flow_name',
                    'scheduled_at',
                ],
            },
        )
        message_id = message.get('id')
        this.save(output_value={
            'message_id': message_id,
        })
        this.flow(
            'Scheduled',
            name='Scheduled execution',
            message_id=message_id,
            wait=False,
        )
        return this.success('requested details')

    message = system.message(message_id)
    response = message.wait().get('response')
    this.log(response=response)
    flow_name = response['flow_name']
    scheduled_at = response['scheduled_at']
    max_iterations = response.get('max_iterations')
    local_tz = response.get('timezone', 'Europe/Vienna')
    this.save(name=f'Scheduled {flow_name}')

    scheduled_at_t = datetime.datetime.strptime(scheduled_at, '%H:%M:%S%z').timetz()
    this.log(scheduled_at_t=scheduled_at_t)
    iterations = 0
    start = datetime.datetime.now(datetime.timezone.utc).timestamp()
    while max_iterations is None or iterations < max_iterations:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone(local_tz))
        this.log(now=now)
        today = now.date()
        this.log(today=today)
        scheduled = datetime.datetime.combine(today, scheduled_at_t)
        scheduled = pytz.timezone(local_tz).localize(scheduled)
        this.log(scheduled=scheduled)
        if scheduled < now:  # next iteration tomorrow
            tomorrow = today + datetime.timedelta(days=1)
            scheduled = datetime.datetime.combine(tomorrow, scheduled_at_t)
            scheduled = pytz.timezone(local_tz).localize(scheduled)
            this.log(scheduled=scheduled)
        scheduled_ts = scheduled.isoformat(sep=' ', timespec='minutes')
        this.log(scheduled_ts=scheduled_ts)
        delta_sec = (scheduled - now).total_seconds()
        this.log(delta_sec=delta_sec)
        this.save(message=scheduled_ts)
        this.sleep(delta_sec)
        iterations += 1
        this.save(message=f'iteration {iterations}/{max_iterations}')
        # Start child execution
        inputs = {
            'start': start,
            'iterations': iterations,
            'max_iterations': max_iterations,
        }
        this.flow(
            flow_name,
            inputs=inputs,
            name=f'{flow_name} iteration #{iterations}',
            wait=False,
        )
        if max_iterations is not None and iterations >= max_iterations:
            break

    return this.success(f'started {iterations} iterations')
