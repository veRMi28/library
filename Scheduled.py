import datetime


def handler(system, this):
    defaults = {
        'scheduled_at': '08:30',
    }
    inputs = this.get('input_value')
    try:
        defaults['flow_name'] = inputs['flow_name']
    except Exception:
        pass

    response = system.message(
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
                    'order': 4,
                },
            },
            'required': [
                'flow_name',
                'scheduled_at',
            ],
        },
    ).wait().get('response')

    this.log(response=response)
    flow_name = response['flow_name']
    scheduled_at = response['scheduled_at']
    max_iterations = response.get('max_iterations')

    scheduled_at_t = datetime.datetime.strptime(scheduled_at, '%H:%M:%S%z').timetz()
    this.log(scheduled_at_t=scheduled_at_t)
    iterations = 0
    start = datetime.datetime.now(datetime.timezone.utc).timestamp()
    while max_iterations is None or iterations < max_iterations:
        now = datetime.datetime.now(datetime.timezone.utc)
        this.log(now=now)
        today = now.date()
        this.log(today=today)
        scheduled = datetime.datetime.combine(today, scheduled_at_t)
        this.log(scheduled=scheduled)
        if scheduled < now:  # next iteration tomorrow
            tomorrow = today + datetime.timedelta(days=1)
            scheduled = datetime.datetime.combine(tomorrow, scheduled_at_t)
            this.log(scheduled=scheduled)
        scheduled_ts = scheduled.isoformat(sep=' ', timespec='minutes')
        this.log(scheduled_ts=scheduled_ts)
        delta_sec = (scheduled - now).total_seconds()
        this.log(delta_sec=delta_sec)
        this.save(message=f'sleeping until {scheduled_ts}')
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
