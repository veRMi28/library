def handler(c):
    # create a task to request input from a user and run it
    task = c.task('INPUT', request='please enter a number').run()
    # access the response
    response = task.getOutputs()['response']
    try:
        # try to convert the string response to a float
        number = float(response)
    except ValueError:
        # if the conversion failed, the response was not a number
        return c.end('error', f'you did not enter a number, but "{response}"')
    # if the conversion succeeded, end with success
    return c.end('success', message=f'thank you! your number was "{number}"')
