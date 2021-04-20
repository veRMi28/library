"""
inputs:
    - json.commit_sha:
        type: str
        required: False
        doc: The commit_sha to fetch. If missing `origin/master` will be fetched.
"""

import os
import yaml
import base64

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    """
    Clone a git repository, create Cloudomation objects from the files.
    All .py files in the flows/ subdirectory will be stored as Flows.
    All .yaml files in the settings/ subdirectory will be stored as Settings.
    All files in the files/ subdirectory will be stored as Files.
    """
    inputs = this.get('input_value')
    # this flow is registered as webhook, triggered by a commit to the
    # repository. The commit sha is passed in .json.commit_sha
    # when started manually, it will sync from master
    try:
        ref = inputs['json']['commit_sha']
    except (KeyError, TypeError):
        ref = 'master'
    # read the connection information of the private repository
    repo_info = system.setting('private git repo').get('value')
    # the git 'get' command fetches the content of the repository.
    # since no files_path is passed, the files will be returned in the
    # output_value of the task
    files = this.task(
        'GIT',
        command='get',
        repository_url=repo_info['repository_url'],
        httpCookie=repo_info['httpCookie'],
        ref=ref,
    ).get('output_value')['files']
    # iterate over all files
    for file_ in files:
        # split the path and filename
        path, filename = os.path.split(file_['name'])
        # split the filename and file extension
        name, ext = os.path.splitext(filename)
        if path == 'flows' and ext == '.py':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # create or update Flow object
            system.flow(name).save(script=text_content)
        elif path == 'settings' and ext == '.yaml':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # load the yaml string in the file content
            value = yaml.safe_load(text_content)
            # create or update Setting object
            system.setting(name).save(value=value)
        elif path == 'files':
            # create or update File object
            # we use the name with the extension
            # pass the base64 encoded binary file content directly
            system.file(filename).save(content=file_['content'], convert_binary=False)

    return this.success('all done')
