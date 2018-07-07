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


def handler(c):
    # Read and validate inputs
    inputs = c.getInputs()
    try:
        questions = inputs['questions']
        assert type(questions) == dict
    except BaseException:
        return c.end('error', 'missing or invalid input "questions"')
    timeout = inputs.get('timeout')
    allow_empty = inputs.get('allow_empty', False)

    # Schedule a task for each question in parallel
    tasks = []
    for field, request in questions.items():
        if type(request) != dict:
            request = {'label': request}
        protect_outputs = None
        if request.get('type') == 'password':
            protect_outputs = ['response']
        task = c.task(
            'TaskInput',
            name=field,
            reference=field,
            retention_time=1,
            request=request['label'],
            timeout=timeout,
            protect_outputs=protect_outputs
        ).runAsync()
        tasks.append(task)

    # wait for any of the tasks to finish
    # read the response
    # remove it from the list
    responses = {}
    while tasks:
        if allow_empty:
            task = c.waitFor(*tasks, unexpected='ignore')
        else:
            task = c.waitFor(*tasks)
        outputs = task.getOutputs()
        field = outputs['reference']
        if not allow_empty and (not outputs or 'response' not in outputs):
            return c.end('error', f'did not get a response for "{field}"')
        if 'response' in outputs:
            responses[field] = outputs['response']
        tasks = [t for t in tasks if t.execution_id != task.execution_id]

    # all questions answerd, set the outputs
    c.setOutput('responses', responses)
