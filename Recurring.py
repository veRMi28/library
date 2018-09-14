import time


def handler(c):
    # Required input: flow_name
    inputs = c.getInputs()
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
    c.setOutput('flow', flow)

    # Optional input: do_query
    do_query = str(inputs.get('do_query', False)) == 'True'
    questions = {}
    c.setOutput('do_query', do_query)

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
        c.setOutput('interval', interval)

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
        c.setOutput('wait', wait)

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
        c.setOutput('max_iterations', max_iterations)

    # Query additional settings
    if do_query and questions:
        input_form = c.flow(
            'Input Form',
            questions=questions,
            allow_empty=True,
        ).run()
        outputs = input_form.getOutputs()
        if interval is None:
            interval = int(outputs['responses'].get('interval', 60))
            c.setOutput('interval', interval)
        if wait is None:
            wait = str(outputs['responses'].get('wait', False)) == 'True'
            c.setOutput('wait', wait)
        if max_iterations is None:
            max_iterations = int(outputs['responses'].get('max_iterations', 0))
            c.setOutput('max_iterations', max_iterations)

    # Loop
    iterations = 0
    start = time.time()
    while max_iterations == 0 or iterations < max_iterations:
        iterations += 1
        # Start child execution
        inputs = {
            'start': start,
            'iterations': iterations,
            'max_iterations': max_iterations,
        }
        child = c.flow(
            flow,
            inputs=inputs,
            name=f'iteration #{iterations}')
        if wait:
            child.run()
            c.sleep(interval)
        else:
            child.runAsync()
            c.sleep_until(start + (iterations * interval))

    c.end('success', f'successfully started {iterations} iterations')
