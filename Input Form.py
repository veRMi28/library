"""
This flow script queries values in parallel.

inputs:
    - questions:
        description:
            | a dict mapping a field name to a question or an options dict.
        required: true
    - timeout:
        description:
            | minutes until the input request expires.
            | specify 0 to disable the timeout.
            | if ommited or None, the default timeout of 10 minutes will be
            | used.
        default: None
    - allow_empty:
        description: if an empty response should be accepted.
        default: False
"""


def handler(system, this):
    # Read and validate inputs
    inputs = this.get('input_value')
    try:
        questions = inputs['questions']
        assert type(questions) == dict
    except Exception:
        return this.error('missing or invalid input "questions"')
    timeout = inputs.get('timeout')
    allow_empty = inputs.get('allow_empty', False)

    # Schedule a task for each question in parallel
    tasks = []
    for field, request in questions.items():
        if type(request) != dict:
            request = {'label': request}
        init = {}
        if request.get('type') == 'password':
            init['protect_outputs'] = ['response']
        task = this.task(
            'INPUT',
            name=field,
            reference=field,
            request=request['label'],
            timeout=timeout,
            init=init,
            type=request.get('type', 'string'),
        ).run_async()
        tasks.append(task)

    # wait for all of the tasks to finish
    this.wait_for(*tasks, return_when=system.return_when.ALL_ENDED)

    # read the responses
    responses = {}
    for task in tasks:
        outputs = task.get('output_value')
        if not allow_empty and (not outputs or 'response' not in outputs):
            return this.end('error', f'did not get a response for "{field}"')
        field = outputs['reference']
        if 'response' in outputs:
            responses[field] = outputs['response']

    # all questions answerd, set the outputs
    this.save(output_value={'responses': responses})
    this.success('all done')
