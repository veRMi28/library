import time


def handler(c):
    # Required input: flow_name or flow_id
    inputs = c.get_inputs()
    try:
        flow = inputs['flow_name']
        assert type(flow) == str
    except BaseException:
        try:
            flow = inputs['flow_id']
            assert type(flow) == int
        except BaseException:
            return c.end(
                'error', 'missing or invalid input "flow_name" or "flow_id"')
    c.set_output('flow', flow)

    # Optional input: do_query
    do_query = str(inputs.get('do_query', False)) == 'True'
    questions = {}
    c.set_output('do_query', do_query)

    # Optional input: use
    default_use = 'delay'
    if 'use' in inputs:
        use = int(inputs['use'])
    elif do_query:
        use = None
        questions['use'] = {
            'label': f'Use "timestamp" or "delay" [{default_use}]',
        }
    else:
        use = default_use
        c.set_output('use', use)

    # Optional input: timestamp
    default_timestamp = int(time.time()) + 60
    if 'timestamp' in inputs:
        timestamp = int(inputs['timestamp'])
    elif do_query:
        timestamp = None
        questions['timestamp'] = {
            'label': f'Unix timestamp when the flow should be started [{default_timestamp}]',
        }
    else:
        timestamp = default_timestamp  # Default value
        c.set_output('timestamp', timestamp)

    # Optional input: delay
    default_delay = 60
    if 'delay' in inputs:
        delay = int(inputs['delay'])
    elif do_query:
        delay = None
        questions['delay'] = {
            'label': f'Delay in seconds after which the flow should be started [{default_delay}]',
        }
    else:
        delay = default_delay  # Default value
        c.set_output('delay', delay)

    # Query additional settings
    if do_query and questions:
        input_form = c.flow(
            'Input Form',
            questions=questions,
            allow_empty=True,
        ).run()
        outputs = input_form.get_outputs()
        if use is None:
            use = outputs['responses'].get('use', default_use)
            c.set_output('use', use)
        if timestamp is None:
            timestamp = int(outputs['responses'].get('timestamp', default_timestamp))
            c.set_output('timestamp', timestamp)
        if delay is None:
            delay = int(outputs['responses'].get('delay', default_delay))
            c.set_output('delay', delay)

    if use == "timestamp":
        c.log(f'sleeping until {timestamp}')
        c.sleep_until(timestamp)
    elif use == "delay":
        c.log(f'sleeping for {delay} seconds')
        c.sleep(delay)

    child = c.flow(
        flow,
        inputs=inputs,
        name='scheduled')
    child.run_async()

    c.end('success', f'successfully started {flow}')
