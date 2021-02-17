import os
import base64
import flow_api


def handler(system: flow_api.System, this: flow_api.Execution):
    """
    Clone a git repository, create Cloudomation objects from the files.
    All .py files in the flows/ subdirectory will be stored as Flows.
    All .yaml files in the settings/ subdirectory will be stored as Settings.
    All files in the files/ subdirectory will be stored as Files.
    
    A pop-up message form will request all necessary user information for the repository.
    
    The inputs are not checked for validity!
    """

    # This is a pop-up message form, it will ask for some information 
    # The last element is an OK-button, after clicking it the 
    # values are passed further and the pop-up message closes.
    git_login_form_response = system.message(
        subject='Input Git repository information to connect',
        message_type = 'POPUP',
        body={
            'type': 'object',
            'properties': {
                'username': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter your username for the GIT repository:',
                    'order': 1,
                },
                'password': {
                    'element': 'password',
                    'type': 'string',
                    'label': 'Enter your password for the GIT repository:',
                    'order': 2,
                },
                # Here an example input is shown in the field, but its value is empty: 
                'repository url': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the URL for the repository you want to clone into Cloudomation:',
                    'example': 'https://repository.url/user/repository.git',
                    'order': 3,
                },
                # Here a default value is provided with the field: 
                'reference': {
                    'element': 'string',
                    'type': 'string',
                    'label': 'Enter the "branch" you want to clone from or a "commit sha":',
                    'default': 'develop',
                    'order': 4,
                },
                'Ok': {
                    'element': 'submit',
                    'label': 'OK',
                    'type': 'boolean',
                    'order': 5,
                },
            },
            'required': [
                'username',
                'password',
                'repository url',
                'reference',
            ],
        },
    ).wait().get('response')
    git_username = git_login_form_response['username'] 
    git_password = git_login_form_response['password']
    git_repo_url = git_login_form_response['repository url']
    git_reference = git_login_form_response['reference']

    # Now we use a "GIT" task.                                      
    # The git 'get' command fetches the content of the repository.
    # Since no files_path is passed, the files will be returned in the
    # output_value of the task
    files = None
    try:
        files = this.task(
            'GIT',
            command='get',
            repository_url=git_repo_url,
            # httpCookie=repo_info.get('httpCookie'),
            ref=git_reference,
            username=git_username,
            password=git_password,
        ).get('output_value')['files']
    except flow_api.exceptions.DependencyFailedError as err:
        files = None
        # send the error message to the output of this execution:
        this.set_output(err)

    # iterate over all files and save them on Cloudomation:
    for file_ in files:
        # split the path and filename
        path, filename = os.path.split(file_['name'])
        # split the filename and file extension
        name, ext = os.path.splitext(filename)
        if 'flows' in path and ext == '.py':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # create or update Flow object
            system.flow(name).save(script=text_content)
        elif 'settings' in path and ext == '.yaml':
            # decode the base64 file content to text
            text_content = base64.b64decode(file_['content']).decode()
            # load the yaml string in the file content
            value = yaml.safe_load(text_content)
            # create or update Setting object
            system.setting(name).save(value=value)
        elif 'files' in path:
            # create or update File object
            # we use the name with the extension
            # pass the base64 encoded binary file content directly
            system.file(filename).save(content=file_['content'], convert_binary=False)

    return this.success('all done')
