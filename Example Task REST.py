def handler(c):
    # create a REST task and run it
    task = c.task('REST', url='https://api.icndb.com/jokes/random').run()
    # access a field of the JSON response
    joke = task.get_outputs()['json']['value']['joke']
    # end with a joke
    c.end('success', message=joke)
