import datetime
import re


def handler(system, this):
    # Required input: flow_name
    inputs = this.get('input_value')
    try:
        flow_name = inputs['flow_name']
    except Exception:
        return this.error('missing input "flow_name"')
    this.log(flow_name=flow_name)

    # Optional input: do_query
    do_query = str(inputs.get('do_query', False)) == 'True'
    questions = {}
    this.log(do_query=do_query)

    # Optional input: interval
    if 'scheduled_at' in inputs:
        scheduled_at = inputs['scheduled_at']
    elif do_query:
        scheduled_at = None
        questions['scheduled_at'] = {
            'label': 'Time when the child execution should be started [08:30+02:00]',
        }
    else:
        scheduled_at = '08:30'  # Default value
        this.log(scheduled_at=scheduled_at)

    # Optional input: max_iterations
    if 'max_iterations' in inputs:
        max_iterations = int(inputs['max_iterations'])
    elif do_query:
        max_iterations = None
        questions['max_iterations'] = {
            'label': 'Maximum number of iterations. 0=no limit [0]',
        }
    else:
        max_iterations = 0  # Default value
        this.log(max_iterations=max_iterations)

    # Query additional settings
    if do_query and questions:
        input_form = this.flow(
            'Input Form',
            questions=questions,
            allow_empty=True,
        ).run()
        outputs = input_form.get('output_value')
        if scheduled_at is None:
            scheduled_at = outputs['responses'].get('scheduled_at', '08:30')
            this.log(scheduled_at=scheduled_at)
        if max_iterations is None:
            max_iterations = int(outputs['responses'].get('max_iterations', 0))
            this.log(max_iterations=max_iterations)

    # CLOUD-1621 TODO: convert to user's timezone
    # currently timezone info can be passed in the `scheduled_at` string:
    # e.g. "16:30+02:00". If no timezone is passed UTC is assumed.
    if re.match(r'\d\d:\d\d\+\d\d:\d\d', scheduled_at):
        pass
    elif re.match(r'\d\d:\d\d', scheduled_at):
        scheduled_at = f'{scheduled_at}:+00:00'
    else:
        return this.error('invalid format for scheduled_at. must be HH:MM (without timezone offset, assumed UTC) or HH:MM+ZZ:ZZ (with timezone offset)')
    scheduled_at_t = datetime.time.fromisoformat(scheduled_at)
    this.log(scheduled_at_t=scheduled_at_t)
    iterations = 0
    start = datetime.datetime.now(datetime.timezone.utc).timestamp()
    while max_iterations == 0 or iterations < max_iterations:
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
            run=True,
            wait=False,
        )
        if max_iterations != 0 and iterations >= max_iterations:
            break

    return this.success(f'started {iterations} iterations')
