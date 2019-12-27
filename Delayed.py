import datetime


def handler(system, this):
    defaults = {
        'delay': '60',
    }
    inputs = this.get('input_value')
    try:
        defaults['flow_name'] = inputs['flow_name']
    except Exception:
        pass

    response = system.message(
        subject='Delayed execution',
        body={
            'type': 'object',
            'properties': {
                'flow_name': {
                    'label': 'Name of the flow which should be started',
                    'element': 'string',
                    'type': 'string',
                    'example': defaults.get('flow_name'),
                    'default': defaults.get('flow_name'),
                    'order': 1,
                },
                'label': {
                    'description': 'You can either specify a time when the execution should be started, or a delay in seconds',
                    'element': 'markdown',
                    'order': 2,
                },
                'time': {
                    'label': 'Time when the child execution should be started',
                    'element': 'time',
                    'type': 'string',
                    'format': 'time',
                    'order': 3,
                },
                'delay': {
                    'label': 'Delay in seconds after which the child execution should be started',
                    'element': 'number',
                    'type': 'number',
                    'example': defaults['delay'],
                    'default': defaults['delay'],
                    'order': 4,
                },
                'start': {
                    'label': 'Start delayed',
                    'element': 'submit',
                    'order': 5,
                },
            },
            'required': [
                'flow_name',
            ],
        },
    ).wait().get('response')

    this.log(response=response)
    flow_name = response['flow_name']
    scheduled_at = response.get('time')
    delay = response.get('delay')

    if scheduled_at is not None:
        scheduled_at_t = datetime.datetime.strptime(scheduled_at, '%H:%M:%S%z').timetz()
        this.log(scheduled_at_t=scheduled_at_t)
        now = datetime.datetime.now(datetime.timezone.utc)
        this.log(now=now)
        today = now.date()
        this.log(today=today)
        scheduled = datetime.datetime.combine(today, scheduled_at_t)
        this.log(scheduled=scheduled)
        if scheduled < now:  # tomorrow
            tomorrow = today + datetime.timedelta(days=1)
            scheduled = datetime.datetime.combine(tomorrow, scheduled_at_t)
            this.log(scheduled=scheduled)
        scheduled_ts = scheduled.isoformat(sep=' ', timespec='minutes')
        this.log(scheduled_ts=scheduled_ts)
        delta_sec = (scheduled - now).total_seconds()
        this.log(delta_sec=delta_sec)
        this.save(message=f'sleeping until {scheduled_ts}')
        this.sleep(delta_sec)
    elif delay is not None:
        this.save(message=f'sleeping for {delay} seconds')
        this.log(f'sleeping for {delay} seconds')
        this.sleep(delay)
    else:
        return this.error('Missing response for "time" or "delay"')

    this.flow(
        flow_name,
        inputs=inputs,
        name=f'delayed {flow_name}',
        wait=False,
    )

    return this.success(f'successfully started {flow_name}')
