import time


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
        this.log(use=use)

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
        this.log(timestamp=timestamp)

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
        this.log(delay=delay)

    # Query additional settings
    if do_query and questions:
        input_form = this.flow(
            'Input Form',
            questions=questions,
            allow_empty=True,
        ).run()
        outputs = input_form.get('output_value')
        if use is None:
            use = outputs['responses'].get('use', default_use)
            this.log(use=use)
        if timestamp is None:
            timestamp = int(outputs['responses'].get('timestamp', default_timestamp))
            this.log(timestamp=timestamp)
        if delay is None:
            delay = int(outputs['responses'].get('delay', default_delay))
            this.log(delay=delay)

    if use == 'timestamp':
        this.save(message=f'sleeping until {timestamp}')
        this.log(f'sleeping until {timestamp}')
        this.sleep_until(timestamp)
    elif use == 'delay':
        this.save(message=f'sleeping for {delay} seconds')
        this.log(f'sleeping for {delay} seconds')
        this.sleep(delay)

    child = this.flow(
        flow_name,
        inputs=inputs,
        name=f'scheduled {flow_name}')
    child.run_async()

    this.success(f'successfully started {flow_name}')
