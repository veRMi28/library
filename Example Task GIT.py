import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # get the contents of a public github repository
    task = this.task(
        'GIT',
        command='get',
        # The url to a public repository
        repository_url='https://github.com/starflows/library/',
        # Get the reference master, I could also specify a sha, another branch or a tag
        ref='master',
    )
    outputs = task.get('output_value')
    # Note that both the name and content of every file is part of the output
    this.log(outputs)

    task2 = this.task(
        'GIT',
        command='get',
        repository_url='https://github.com/starflows/library/',
        files_path='flow_library',
        ref='v2',
    )
    outputs = task2.get('output_value')
    # Here there are no files in the output
    this.log(outputs)
    # But they are saved to cloudomation:
    files = system.files(dir='flow_library')
    for file in files:
        this.log(file)
    return this.success('all done')
