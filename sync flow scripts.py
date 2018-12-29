import yaml
import os


def handler(system, this):
    inputs = this.get('input_value')
    # this flow is registered as webhook, triggered by a commit to the
    # repository. The commit sha is passed in .data_json.commit_sha
    # when started manually, it will sync from master
    try:
        commit_sha = inputs['data_json']['commit_sha']
    except Exception:
        commit_sha = 'master'
    # read the connection information of the private repository
    repo_info = system.setting('private git repo').get('value')
    # the git 'get' command ensures the content of the repository in a local
    # folder. it will clone or fetch and merge.
    this.task(
        'GIT',
        command='get',
        repository_url=repo_info['repository_url'],
        repository_path='repo',
        httpCookie=repo_info['httpCookie'],
        ref=commit_sha,
    ).run()
    # list all flows from the repository
    # this call will return a list of File objects
    files = system.files(dir='repo/flows', glob='**/*.py')
    this.log(files=files)
    for file in files:
        # access the path field of the file object
        path = file.get('path')
        # ignore any subdirectory and extension
        name, ext = os.path.splitext(os.path.basename(path))
        # access the content of the file
        content = file.get('content')
        # create a new Flow object
        system.flow(name=name, script=content)
    # repeat the same for yaml files and Setting objects
    files = system.files(dir='repo/settings', glob='**/*.yaml')
    this.log(files=files)
    for file in files:
        path = file.get('path')
        name, ext = os.path.splitext(os.path.basename(path))
        content = file.get('content')
        value = yaml.safe_load(content)
        system.setting(name=name, value=value)
    this.success('all done')
