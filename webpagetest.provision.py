from datetime import date
from Crypto.PublicKey import RSA
import contextlib
import json

import flow_api

'''
Creates a server called webpagetest-server-template and stores it as a snapshot in gcloud
Inputs:
    gcloud_connection: <string> name of the connection stored in the cloudomation workspace    
'''

def handler(system: flow_api.System, this: flow_api.Execution):
    inputs = this.get('input_value')
    gcloud_connection = inputs.get('gcloud_connection')
    project_id = system.connection(gcloud_connection).get('value').get('key').get('project_id')
    if project_id is None or gcloud_connection is None:
        return this.error('Missing inputs')

    webpagetestserver_template_setting = system.setting('webpagetest-server-template')
    webpagetestserver_template_setting.acquire(timeout=None)

    instance_list = this.connect(
        gcloud_connection,
        name='find webpagetest-server-template',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='list',
        params={
            'filter': 'name=webpagetest-server-template',
            'project': project_id,
            'zone': 'europe-west1-b',
        },
    ).get('output_value')
    if len(instance_list['result'].get('items', [])) > 0:
        this.connect(
            gcloud_connection,        
            name='delete webpagetest-template',
            api_name='compute',
            api_version='v1',
            collection='instances',
            request='delete',
            params={
                'instance': 'webpagetest-server-template',
                'project': project_id,
                'zone': 'europe-west1-b',
            },
        )
        for _ in range(60):
            instance_list = this.connect(
                gcloud_connection,        
                name='find webpagetest-server-template',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='list',
                params={
                    'filter': f'name=webpagetest-server-template',
                    'project': project_id,
                    'zone': 'europe-west1-b',

                },
            ).get('output_value')
            if len(instance_list['result'].get('items', [])) == 0:
                break
            this.sleep(1)
        else:
            return this.error('old webpagetest-server-template still exists after 60 tries')

    images = this.connect(
        gcloud_connection,
        name='find ubuntu image name',
        api_name='compute',
        api_version='v1',
        collection='images',
        request='list',
        params={
            'project': 'ubuntu-os-cloud'
        }
    ).load('output_value')['result']['items']
    image_name = None
    for image in images:
        with contextlib.suppress(KeyError):
            if image['deprecated']['state'] == 'DEPRECATED':
                continue
        if image['name'].startswith('ubuntu-1804-bionic-'):
            image_name = image['name']
            break

    setup_user_key = RSA.generate(2048)
    setup_user_priv = setup_user_key.export_key().decode()
    setup_user_pub = setup_user_key.publickey().export_key(format='OpenSSH').decode()
    setup_user_key = None

    webpagetest_user_key = RSA.generate(2048)
    webpagetest_user_priv = webpagetest_user_key.export_key().decode()
    webpagetest_user_pub = webpagetest_user_key.publickey().export_key(format='OpenSSH').decode()
    webpagetest_user_key = None

    webpagetest_server_startup_script = system.file('webpagetest-server-template-startup.sh').get('content')
    webpagetest_server_startup_script = webpagetest_server_startup_script.format(
        setup_user_pub=setup_user_pub,
        webpagetest_user_pub=webpagetest_user_pub,
    )
    webpagetest_server_config_str = system.file('webpagetest-server-template.json').get('content')
    webpagetest_server_config_str.replace('{PROJECT_ID}', project_id)
    webpagetest_server_config = json.loads(webpagetest_server_config_str)
    webpagetest_server_config['metadata']['items'][0]['value'] = webpagetest_server_startup_script
    webpagetest_server_config['name'] = 'webpagetest-server-template'
    webpagetest_server_config['disks'][0]['deviceName'] = 'webpagetest-server-template'
    webpagetest_server_config['disks'][0]['initializeParams']['sourceImage'] = f'projects/ubuntu-os-cloud/global/images/{image_name}'

    operation = this.connect(
        gcloud_connection,        
        name='launch webpagetest-server-template',
        api_name='compute',
        api_version='v1',
        collection='instances',
        request='insert',
        params={
            'body': webpagetest_server_config,
            'project': project_id,
            'zone': 'europe-west1-b',
        },
    ).get('output_value')['result']
    this.flow(
        'google_operation_wait',
        operation=operation,
    )

    try:
        for _ in range(60):
            instance_list = this.connect(
                gcloud_connection,        
                name='find webpagetest-server-template',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='list',
                params={
                    'filter': 'name=webpagetest-server-template',
                    'project': project_id,
                    'zone': 'europe-west1-b',
                },
            ).get('output_value')
            if len(instance_list['result'].get('items', [])) != 0:
                break
            this.sleep(1)
        else:
            return this.error('did not find webpagetest server template within 60 tries')
        external_ip = instance_list['result']['items'][0]['networkInterfaces'][0]['accessConfigs'][0]['natIP']

        failed_tries = []
        for _ in range(60):
            this.sleep(1)
            guest_attribute_task = this.connect(
                gcloud_connection,        
                name='get webpagetest-server-template hostkey',
                api_name='compute',
                api_version='beta',
                collection='instances',
                request='getGuestAttributes',
                params={
                    'instance': 'webpagetest-server-template', 
                    'queryPath': 'hostkeys/ssh-rsa',
                    'project': project_id,
                    'zone': 'europe-west1-b',
                },
                wait=system.return_when.ALL_ENDED,
            )
            if guest_attribute_task.load('status') == 'ENDED_SUCCESS':
                break
            failed_tries.append(guest_attribute_task)
        else:
            return this.error('did not find hostkey within 60 tries')
        for failed_try in failed_tries:
            failed_try.delete()
        hostkey = guest_attribute_task.get('output_value')['result']['queryValue']['items'][0]['value']

        system.connection('webpagetestserver-setup').save(
            connection_type='SSH',
            value={
                'key': setup_user_priv,
                'username': 'setup-user',
                'hostname': external_ip,
                'hostkey': hostkey,
            },
        )
        system.connection('webpagetestserver').save(
            connection_type='SSH',
            value={
                'key': webpagetest_user_priv,
                'username': 'webpagetest-user',
                'hostname': external_ip,
                'hostkey': hostkey,
            },
        )
        system.connection('webpagetestserver-copy').save(
            connection_type='SCP',
            value={
                'key': webpagetest_user_priv,
                'username': 'webpagetest-user',
                'hostname': external_ip,
                'hostkey': hostkey,
            },
        )

        webpagetestserver_template = {
            'hostname': external_ip,
            'hostkey': hostkey,
            'setup-user': {
                'username': 'setup-user',
                'ssh-key': setup_user_priv,
                'public-key': setup_user_pub,
            },
            'webpagetest-user': {
                'username': 'webpagetest-user',
                'ssh-key': webpagetest_user_priv,
                'public-key': webpagetest_user_pub,
            },
        }            
        
        for _ in range(10):
            try:
                this.connect(
                    'webpagetestserver-setup',
                    script="""
                        sudo apt-get update
                        sudo apt-get install -y --no-install-recommends python-pip python3-pip
                        sudo apt-get install -y --no-install-recommends build-essential python3-dev iftop iotop zip unzip
                        # DO NOT remove python3-cryptography! or instance will not be able to setup networking on boot
                        # sudo apt-get remove -y python3-cryptography
                        """,
                    name='install packages',
                )
            except Exception:
                this.sleep(3)
            else:
                break
        else:
            return this.error('failed to ssh to webpagetestserver-template within 10 tries')

        this.connect(
            'webpagetestserver',
            script="""
                pip install wheel setuptools
                pip3 install wheel setuptools
                pip3 install alembic psycopg2-binary
                """,
            name='install pip packages',
        )

        this.connect(
            'webpagetestserver-setup',
            script="""
                set +e
                ssh -V
                ret=$?
                set -e
                if [ "$ret" -ne "0" ]; then
                    sudo apt-get install -y --no-install-recommends openssh-client
                fi
                """,
            name='install openssh client',
        )

        this.connect(
            'webpagetestserver-setup',
            script="""
                set +e
                jq -V
                ret=$?
                set -e
                if [ "$ret" -ne "0" ]; then
                    sudo apt-get install -y --no-install-recommends jq
                fi
                set +e
                jq -V
                ret=$?
                set -e
                if [ "$ret" -ne "0" ]; then
                    sudo snap install jq
                fi
                """,
            name='install jq',
        )

        this.connect(
            'webpagetestserver-setup',
            script="""
                set +e
                yq -V
                ret=$?
                set -e
                if [ "$ret" -ne "0" ]; then
                    sudo snap install yq
                fi
                """,
            name='install yq',
        )

        this.connect(
            'webpagetestserver-setup',
            script="""
                set +e
                docker --version
                ret=$?
                set -e
                if [ "$ret" -ne "0" ]; then
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sh get-docker.sh
                    RELEASE=$(lsb_release -is | tr '[:upper:]' '[:lower:]')
                    sudo apt-get install -y --no-install-recommends \\
                        apt-transport-https \\
                        ca-certificates \\
                        curl \\
                        gnupg2 \\
                        software-properties-common
                    curl -fsSL https://download.docker.com/linux/${RELEASE}/gpg | sudo apt-key add -
                    sudo add-apt-repository \\
                        "deb [arch=amd64] https://download.docker.com/linux/${RELEASE} \\
                        $(lsb_release -cs) \\
                        stable"
                    sudo apt-get update
                    sudo apt-get install -y --no-install-recommends docker-ce
                fi
                sudo usermod -a -G docker webpagetest-user
                """,
            name='install docker',
        )

        this.connect(
            'webpagetestserver',
            name='create webpagetest folders',
            script="""
                mkdir -p webpagetest/server
                mkdir -p webpagetest/agent
            """,
        )

        this.connect(
            'webpagetestserver-copy',
            name='copy webpagetest server Dockerfile',
            src='cloudomation:webpagetest-server-Dockerfile',
            dst='webpagetest/server/Dockerfile',
        )

        this.connect(
            'webpagetestserver-copy',
            name='copy webpagetest server locations.ini',
            src='cloudomation:webpagetest-server-locations.ini',
            dst='webpagetest/server/locations.ini',
        )

        this.connect(
            'webpagetestserver-copy',
            name='copy webpagetest agent Dockerfile',
            src='cloudomation:webpagetest-agent-Dockerfile',
            dst='webpagetest/agent/Dockerfile',
        )

        this.connect(
            'webpagetestserver-copy',
            name='copy webpagetest agent script.sh',
            src='cloudomation:webpagetest-agent-script.sh',
            dst='webpagetest/agent/script.sh',
        )
        
        this.connect(
            'webpagetestserver',
            name='create webpagetest server and agent',
            input_value={
                'script_timeout':600
            },
            script="""
                pushd webpagetest/server
                docker build -t wpt-server .
                docker run -d -p 4000:80 --restart unless-stopped wpt-server
                popd
                pushd webpagetest/agent
                chmod u+x script.sh
                docker build -t wpt-agent .
                docker run -d -p 4001:80 \\
                    --restart unless-stopped \\
                    --network="host" \\
                    -e "SERVER_URL=http://localhost:4000/work/" \\
                    -e "LOCATION=Test" \\
                    wpt-agent
            """,
        )

        this.connect(
            gcloud_connection,        
            name='stop webpagetest-server-template',
            api_name='compute',
            api_version='v1',
            collection='instances',
            request='stop',
            params={
                'instance': 'webpagetest-server-template',
                'project': project_id,
                'zone': 'europe-west1-b',
            },
        )

        try:
            operation = this.connect(
                gcloud_connection,
                name='delete old webpagetest-server-template snapshot',
                api_name='compute',
                api_version='v1',
                collection='snapshots',
                request='delete',
                params={
                    'snapshot': 'webpagetest-server-template',
                    'project': project_id,
                },
            ).get('output_value')['result']
            this.flow(
                'google_operation_wait',
                operation=operation,
            )
        except Exception:
            pass

        today = date.today()
        operation = this.connect(
            gcloud_connection,        
            name='create webpagetest-server-template snapshot',
            api_name='compute',
            api_version='v1',
            collection='disks',
            request='createSnapshot',
            params={
                'disk': 'webpagetest-server-template',
                'body': {
                    'name': 'webpagetest-server-template',
                    'description': f'auto-generated at {today} by setup webpagetest server',
                    'storageLocations': ['europe-west1'],
                },
                'project': project_id,
                'zone': 'europe-west1-b',
            },
        ).get('output_value')['result']
        this.flow(
            'google_operation_wait',
            operation=operation,
        )

        webpagetestserver_template.pop('hostname')
        webpagetestserver_template.pop('hostkey')
        webpagetestserver_template_setting.save(value=webpagetestserver_template)
        webpagetestserver_template_setting.release()

    except Exception as ex:
        this.save(message=repr(ex))
        if this.get('input_value').get('interactive'):
            this.sleep(120)
            # this.pause()
        raise
    finally:
        instance_list = this.connect(
            gcloud_connection,        
            name='find webpagetest-server-template',
            api_name='compute',
            api_version='v1',
            collection='instances',
            request='list',
            params={
                'filter': f'name=webpagetest-server-template',
                'project': project_id,
                'zone': 'europe-west1-b'
            },
        ).get('output_value')
        if len(instance_list['result'].get('items', [])) > 0:
            this.connect(
                gcloud_connection,        
                name='delete webpagetest-server-template',
                api_name='compute',
                api_version='v1',
                collection='instances',
                request='delete',
                params={
                    'instance': 'webpagetest-server-template',
                    'project': project_id,
                    'zone': 'europe-west1-b',
                },
            )
            while True:
                instance_list = this.connect(
                    gcloud_connection,        
                    name='find webpagetest-server-template',
                    api_name='compute',
                    api_version='v1',
                    collection='instances',
                    request='list',
                    params={
                        'filter': 'name=webpagetest-server-template',
                        'project': project_id,
                        'zone': 'europe-west1-b',
                    },
                ).get('output_value')
                if len(instance_list['result'].get('items', [])) == 0:
                    break
                this.sleep(1)

    return this.success('all done')
