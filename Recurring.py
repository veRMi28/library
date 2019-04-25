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

    # Optional input: interval
    if 'interval' in inputs:
        interval = int(inputs['interval'])
    elif do_query:
        interval = None
        questions['interval'] = {
            'label': 'Interval of recurring execution in seconds [60]',
        }
    else:
        interval = 60  # Default value
        this.log(interval=interval)

    # Optional input: wait
    if 'wait' in inputs:
        wait = str(inputs['wait']) == 'True'
    elif do_query:
        wait = None
        questions['wait'] = {
            'label': 'Wait for child executions to finish [False]',
        }
    else:
        wait = False  # Default value
        this.log(wait=wait)

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
        if interval is None:
            interval = int(outputs['responses'].get('interval', 60))
            this.log(interval=interval)
        if wait is None:
            wait = str(outputs['responses'].get('wait', False)) == 'True'
            this.log(wait=wait)
        if max_iterations is None:
            max_iterations = int(outputs['responses'].get('max_iterations', 0))
            this.log(max_iterations=max_iterations)

    # Loop
    iterations = 0
    start = time.time()
    while max_iterations == 0 or iterations < max_iterations:
        iterations += 1
        this.save(message=f'iteration {iterations}/{max_iterations}')
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
        )
        if wait:
            try:
                child.run()
            except Exception:
                this.log(f'iteration #{iterations} failed')
        else:
            child.run_async()
        if max_iterations != 0 and iterations >= max_iterations:
            break
        if wait:
            this.sleep(interval)
        else:
            this.sleep_until(start + (iterations * interval))

    return this.success(f'started {iterations} iterations')
