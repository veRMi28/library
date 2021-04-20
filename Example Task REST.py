import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # create a REST task and run it
    task = this.task('REST', url='https://api.icndb.com/jokes/random')
    # access a field of the JSON response
    joke = task.get('output_value')['json']['value']['joke']
    # end with a joke
    return this.success(message=joke)
