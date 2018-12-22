def handler(c):
    # get the contents of a public github repository
    c.task(
        'GIT',
        command='get',
        # Specify the url of the repository - note that all files from that
        # repository will be copied
        repository_url='https://github.com/starflows/library/',
        # the repository path is where the files from git are stored in
        # Cloudomation
        repository_path='flows_from_git',
        # I want to get the master branch - I could also specify a tag or
        # commit sha
        ref='master',
    ).run()
    # Listing the files I got from git in the repository I specified on the
    # Cloudomation platform
    files = c.list_dir('flows_from_git')
    # I set the output to the list of files
    c.set_output('git files', files)
    c.success(message='all done')
