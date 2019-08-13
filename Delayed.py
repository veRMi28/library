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
    this.log(do_query=do_query)

    # Optional input: use
    default_use = 'delay'
    if 'use' in inputs:
        use = inputs['use']
    elif do_query:
        use = this.task(
            'INPUT',
            request=f'Use "timestamp" or "delay" [{default_use}]',
        ).get('output_value').get('response', default_use)
    else:
        use = default_use
        this.log(use=use)

    if use == 'timestamp':
        # Optional input: timestamp
        default_timestamp = int(time.time()) + 60
        if 'timestamp' in inputs:
            timestamp = int(inputs['timestamp'])
        elif do_query:
            timestamp = this.task(
                'INPUT',
                request=f'Unix timestamp when the flow should be started [{default_timestamp}]',
            ).get('output_value').get('response', default_timestamp)
        else:
            timestamp = default_timestamp  # Default value
            this.log(timestamp=timestamp)
    elif use == 'delay':
        # Optional input: delay
        default_delay = 60
        if 'delay' in inputs:
            delay = int(inputs['delay'])
        elif do_query:
            delay = this.task(
                'INPUT',
                request=f'Delay in seconds after which the flow should be started [{default_delay}]',
            ).get('output_value').get('response', default_delay)
        else:
            delay = default_delay  # Default value
            this.log(delay=delay)

    if use == 'timestamp':
        this.save(message=f'sleeping until {timestamp}')
        this.log(f'sleeping until {timestamp}')
        this.sleep_until(timestamp)
    elif use == 'delay':
        this.save(message=f'sleeping for {delay} seconds')
        this.log(f'sleeping for {delay} seconds')
        this.sleep(delay)
    else:
        return this.error(f'Invalid value for "use": "{use}"')

    this.flow(
        flow_name,
        inputs=inputs,
        name=f'delayed {flow_name}',
        wait=False,
    )

    return this.success(f'successfully started {flow_name}')
