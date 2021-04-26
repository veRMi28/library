"""
inputs:
    - message_id:
        type: str
        required: False
        doc: |
            The UUID of the message form the user was asked to fill in.
            If unset, the flow will create a message form.
    - flow_name:
        type: str
        required: False
        doc: the name of the flow script to be scheduled
"""

import datetime, pytz
import dateutil.relativedelta

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    """
    Create a message form to ask for details and schedule a flow
    """
    inputs = this.get('input_value') or {}
    message_id = inputs.get('message_id')

    if message_id is None:
        defaults = {
            'scheduled_at_day': 1,
            'scheduled_at_time': '08:30',
        }
        try:
            defaults['flow_name'] = inputs['flow_name']
        except (KeyError, TypeError):
            pass
        message = system.message(
            subject='Monthly scheduled execution',
            body={
                'type': 'object',
                'properties': {
                    'flow_name': {
                        'label': 'Name of the flow which should be scheduled monthly',
                        'element': 'string',
                        'type': 'string',
                        'example': defaults.get('flow_name'),
                        'default': defaults.get('flow_name'),
                        'order': 1,
                    },
                    'scheduled_at_day': {
                        'label': 'Day of the month when the child execution should be started',
                        'element': 'number',
                        'type': 'number',
                        'default': defaults['scheduled_at_day'],
                        'order': 2,
                    },
                    'scheduled_at_time': {
                        'label': 'Time when the child execution should be started',
                        'element': 'time',
                        'type': 'string',
                        'format': 'time',
                        'default': defaults['scheduled_at_time'],
                        'order': 3,
                    },
                    'max_iterations': {
                        'label': 'Maximum number of iterations (unlimited if omitted)',
                        'element': 'number',
                        'type': 'number',
                        'order': 4,
                    },
                    'start': {
                        'label': 'Start monthly schedule',
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 5,
                    },
                },
                'required': [
                    'flow_name',
                    'scheduled_at_day',
                    'scheduled_at_time',
                ],
            },
        )
        message_id = message.get('id')
        this.save(output_value={
            'message_id': message_id,
        })
        this.flow(
            'Scheduled monthly',
            name='Monthly scheduled execution',
            message_id=message_id,
            wait=False,
        )
        return this.success('requested details')

    message = system.message(message_id)
    response = message.wait().get('response')
    this.log(response=response)
    flow_name = response['flow_name']
    scheduled_at_day = response['scheduled_at_day']
    scheduled_at_time = response['scheduled_at_time']
    local_tz = response.get('timezone', 'Europe/Vienna')
    max_iterations = response.get('max_iterations')
    this.save(name=f'Scheduled {flow_name}')

    try:
        scheduled_at_time_t = datetime.datetime.strptime(scheduled_at_time, '%H:%M:%S%z').timetz()
    except ValueError:
        scheduled_at_time_t = datetime.datetime.strptime(scheduled_at_time, '%H:%M:%S').timetz()
    this.log(scheduled_at_time_t=scheduled_at_time_t)
    iterations = 0
    start = datetime.datetime.now(datetime.timezone.utc).timestamp()
    while max_iterations is None or iterations < max_iterations:
        now = datetime.datetime.now(datetime.timezone.utc)
        if scheduled_at_time_t.tzinfo is None:
            now = now.astimezone(pytz.timezone(local_tz))
        this.log(now=now)
        today = now.date()
        this.log(today=today, day=today.day)
        scheduled_at_day_t = today.replace(day=scheduled_at_day)
        scheduled_t = datetime.datetime.combine(scheduled_at_day_t, scheduled_at_time_t)
        if scheduled_t.tzinfo is None or scheduled_t.tzinfo.utcoffset(scheduled_t) is None:
            scheduled_t = pytz.timezone(local_tz).localize(scheduled_t)
        if scheduled_t < now:
            scheduled_t += dateutil.relativedelta.relativedelta(months=1)
        this.log(scheduled_t=scheduled_t)

        scheduled_ts = scheduled_t.isoformat(sep=' ', timespec='minutes')
        this.log(scheduled_ts=scheduled_ts)
        delta_sec = (scheduled_t - now).total_seconds()
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
