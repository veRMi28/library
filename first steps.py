import textwrap
import time
import yaml
import datetime
from xml.sax.saxutils import unescape


def handler(system, this):
    DT_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
    number_of_steps = 12
    user_name = system.get_own_user().get('name')
    client_name = system.get_own_client().get('name')
    user_name = user_name[0].upper() + user_name[1:]
    execution_name = ''
    execution_status = ''
    output_value_str = ''
    setting_id = None
    setting_name = ''
    text = ''
    iterations = 0
    delay = 0
    file_content = ''
    message = ''
    time_out = 30*60
    poll_interval = 10

    def get_message(step):
        messages = [
            textwrap.dedent( # step 1
                f'''
                ### Hi {user_name}, Welcome to Cloudomation!

                This wizard will guide you through some first steps to explore the functionality of Cloudomation.
                You will be given a task and the wizard continues once the task is done.

                If at any time you want to view the instructions again, switch to the <strong><i class="fa fa-envelope-o"></i> Messages</strong> resource.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your first task:</strong>
                    <div><i class="fa fa-check-square-o"></i> Close this message by pressing "OK".</div>
                </div>
                '''),
            textwrap.dedent( # step 2
                f'''
                The Cloudomation user-interface uses the following layout:

                <div class="p-row p-justify-center mb-3">
                    <div class="p-col" style="border: 1px solid black; width: 300px; height: 150px">
                        <div class="p-row p-align-center p-justify-center p-1 bg-blue text-blue-contrast">Header</div>
                        <div class="p-row c-grow">
                            <div class="p-row p-align-center p-justify-center p-1 bg-green text-green-contrast" style="width: 15%; writing-mode: vertical-lr">Navigation</div>
                            <div class="p-col c-grow">
                                <div class="p-row p-align-center p-justify-center p-1 bg-yellow text-yellow-contrast">Action bar</div>
                                <div class="p-row c-grow p-align-center p-justify-center p-1 bg-light-darker text-light-darker-contrast">Main area</div>
                            </div>
                        </div>
                    </div>
                </div>

                The navigation is structured in levels:

                - Categories: e.g. **- App - <i class="fa fa-chevron-down"></i>**
                    - Resources: e.g. **<i class="fa fa-desktop"></i> Executions**
                        - Opened records: e.g. <i class="fa fa-file-code-o"></i> my first flow

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Familiarize yourself with the components of the user-interface.</div>
                    <div><i class="fa fa-check-square-o"></i> Select the <strong><i class="fa fa-code"></i> Flows</strong> resource in the <strong>- App -</strong> category.</div>
                    <div><i class="fa fa-check-square-o"></i> Create a new flow by pressing <span class="text-primary"><i class="fa fa-file-o"></i> New</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 3
                f'''
                A flow contains the automation logic which is processed by Cloudomation when the flow is run.

                You can learn more about flows in the [Flows](/documentation/Flows){{ext}} documentation.

                The newly created flow is opened for you.
                You can see all opened flow records below the <strong><i class="fa fa-code"></i> Flows</strong> resource in the menu on the left.

                Flows contain two important fields:
                - The flow name
                - The flow script

                Flow names must be unique among all flows.

                The flow script has to be Python code with a handler function.
                There are many Python tutorials out there, for example [The Python Tutorial](https://docs.python.org/3/tutorial/){{ext}} by the Python Software Foundation

                <div class="alert alert-info p-row p-align-center">
                    <i class="fa fa-info fa-2x text-info pr-3"></i> The rest of the wizard assumes basic understanding of Python syntax.
                </div>

                The new flow script already contains the handler function and some boilerplate.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Change the name of the flow to something more useful, like "my first flow".</div>
                    <div><i class="fa fa-check-square-o"></i> Replace the script with the following:
                        <pre class="ml-3"><code>def handler(system, this):
                    this.log('Hello {user_name}!')
                    return this.success('all done')</code></pre>
                    </div>
                    <div><i class="fa fa-check-square-o"></i> Create an execution of the flow by pressing <span class="text-success"><i class="fa fa-play"></i> Try</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 4
                f'''
                **Congratulations!**
                
                Your execution `{execution_name}` just ended with status `{execution_status}`.
                When you pressed <span class="text-success"><i class="fa fa-play"></i> Try</span>, the user-interface switched to the executions list.

                **The difference between <span class="text-success"><i class="fa fa-play"></i> Try</span> and <span class="text-success"><i class="fa fa-play"></i> Run</span>**
                
                Both actions start the execution of your flow. For development, you can use <span class="text-success"><i class="fa fa-play"></i> Try</span> in the browser.
                <span class="text-success"><i class="fa fa-play"></i> Run</span> is meant for productive use.
                
                **Executions**

                You can see an overview of all running executions in the execution list.
                By clicking on the name of your execution, you open the execution record view.
                When scrolling down in the execution record view, you will see the “Outputs” field which contains:
                
                ```yaml
{textwrap.indent(output_value_str,'                ')}
                ```
                
                ---

                Next, let's look at the <strong><i class="fa fa-sliders"></i> Settings</strong> resource.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Select the <strong><i class="fa fa-sliders"></i> Settings</strong> resource.</div>
                    <div><i class="fa fa-check-square-o"></i> Create a new setting by pressing <span class="text-primary"><i class="fa fa-file-o"></i> New</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 5
                f'''
                Just like flows, settings contain two important fields:
                - The setting name
                - The setting value

                Setting names must be unique among all settings.

                The setting value must be a valid [YAML document](https://learnxinyminutes.com/docs/yaml/){{ext}}.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Change the name of the setting to something more useful, like "test setting".</div>
                    <div><i class="fa fa-check-square-o"></i> Replace the setting's value with the following:
                        <pre class="ml-3"><code>text: Hello {user_name}!
                iterations: 10
                delay: 6</code></pre>
                    </div>
                    <div><i class="fa fa-check-square-o"></i> Save the setting by pressing <span class="text-primary"><i class="fa fa-save"></i> Save</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 6
                f'''
                Let's create another flow which uses the newly created setting.

                This flow will read the values of `text`, `iterations`, and `delay` from the setting.

                With the values you put in the setting it will log the text "{text}" "{iterations}" times with a delay of "{delay}" seconds.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Create a new flow.</div>
                    <div><i class="fa fa-check-square-o"></i> Paste the following script:
                        <pre class="ml-3"><code>def handler(system, this):
                    # read the value of the setting record
                    test_setting = system.setting('{setting_name}').get('value')
                    # loop `iterations` times
                    for i in range(test_setting['iterations']):
                        # log the text
                        this.log(test_setting['text'])
                        # sleep for `delay` seconds
                        this.sleep(test_setting['delay'])
                    return this.success('all done')</code></pre>
                    </div>
                    <div><i class="fa fa-check-square-o"></i> Create an execution of the flow by pressing <span class="text-success"><i class="fa fa-play"></i> Try</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 7
                f'''
                Your execution "{execution_name}" is now running. It will take about {iterations * delay} seconds to end.

                In the <strong><i class="fa fa-fw fa-desktop"></i> Executions</strong> resource you can see the list of all your executions.
                There you can monitor the current status of your executions.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Switch to the <strong><i class="fa fa-fw fa-desktop"></i> Executions</strong> resource. You'll see a list of all your executions.</div>
                    <div><i class="fa fa-check-square-o"></i> Select your execution by checking it in the list: <i class="fa fa-check-square-o"></i></div>
                    <div><i class="fa fa-check-square-o"></i> Pause the execution by pressing <span class="text-primary"><i class="fa fa-pause"></i> Pause</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 8
                f'''
                Let's recap what we've already seen:

                **The user-interface**

                - Layout: There are four main areas: header, navigation, main area, and action bar.
                - The **- App -** category lists resources: Executions, Flows, Settings, and others.
                - Selecting a resource shows a list of all records in the main area.
                - It is possible to check records in the list view and perform actions on _all_ checked records at once.
                - In the record view more details are seen and the record can be modified.

                **The resources**

                - Flows contain automation logic.
                - Executions are created by "running" or "trying" a flow.
                - Flows can access settings to read or write values.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your task:</strong>
                    <div><i class="fa fa-check-square-o"></i> Close this message by pressing "OK".</div>
                </div>
                '''),
            textwrap.dedent( # step 9
                f'''
                Now, let's see how to work with files.
                
                The **Files** section is right beneath the settings section on the left.

                In this section, you can store arbitrary files like shell scripts, markup files, zip files etc.
                All these files can be loaded and manipulated through flow scripts.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Create a file by pressing <span class="text-primary"><i class="fa fa-file-o"></i> New</span> in the action bar.</div>
                    <div><i class="fa fa-check-square-o"></i> Rename the file to <code>myfile.txt</code> and write something into the text field and press <span class="text-primary"><i class="fa fa-save"></i> Save</span> in the action bar.</div>                    
                    <div><i class="fa fa-check-square-o"></i> Create a new flow and paste the following script into the code editor:
                    <pre class="ml-3"><code>def handler(system, this):
                    # read the value of the file
                    read_file = system.file(
                        name='myfile.txt'
                    )
                    # print contents of the file to the log output
                    this.log(read_file.get('content'))
                    this.success(message='all done')</code></pre>
                    </div>
                    <div><i class="fa fa-check-square-o"></i> Create an execution of the flow by pressing <span class="text-success"><i class="fa fa-play"></i> Try</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 10
                f'''
                You can see the content of the file in the **Outputs** section in the execution <code>{execution_name}</code>:
                <pre class="ml-3"><code>{file_content}</code></pre>

                You can learn more about files under [Files](/documentation/File%20handling%20with%20Cloudomation){{ext}} in the documentation.

                ---

                Next, let's explore tasks.

                As already covered, flows contain the automation logic.
                Tasks on the other hand provide a way to access outside systems.
                There are several task types available, each of which specializes on a certain protocol to talk with outside systems.

                The `REST` task for example can be used to communicate with any REST service. Let's try!

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your tasks:</strong>
                    <div><i class="fa fa-check-square-o"></i> Create a new flow.</div>
                    <div><i class="fa fa-check-square-o"></i> Paste the following script:
                    <pre><code>def handler(system, this):
                    # create a REST task and run it
                    task = this.task('REST', url='https://api.icndb.com/jokes/random')
                    # access a field of the JSON response
                    joke = task.get('output_value')['json']['value']['joke']
                    # end with a joke
                    return this.success(message=joke)</code></pre>
                    </div>
                    <div><i class="fa fa-check-square-o"></i> Create an execution of the flow by pressing <span class="text-success"><i class="fa fa-play"></i> Try</span> in the action bar.</div>
                </div>
                '''),
            textwrap.dedent( # step 11
                f'''
                Your execution `{execution_name}` ended with the message:

                    {message}

                Aside from learning something fascinating about Chuck Norris, we also used two additional important features of Cloudomation:

                - Child executions
                - Execution inputs and outputs

                Let's look at line 3 of the flow `{execution_name}` you've just created:

                ```python
                task = this.task('REST', url='https://api.icndb.com/jokes/random')
                ```

                There are several things to notice:

                - `this.task` instructs Cloudomation to create a task execution which is a child of the currently running execution.
                - `REST` specifies which task type to use.
                - `url=...` passes an input value named `url` to the task.

                All task types provide access to outside systems and accept a different set of inputs.
                You can learn more about the available task types in the [Tasks](/documentation/Tasks){{ext}} documentation.

                Once the child execution ends, your flow continues running.
                The child execution provides output values which can be used by your flow.
                This we can see in line 5:

                ```python
                joke = task.get('output_value')['json']['value']['joke']
                ```

                - `task.get` instructs Cloudomation to read a field of the child execution.
                - `output_value` specifies which field to read.
                - `['json']['value']['joke']` selects the part of the output value we are interested in.

                <div class="alert alert-primary">
                    <strong class="d-block pb-1">Your task:</strong>
                    <div><i class="fa fa-check-square-o"></i> Close this message by pressing "OK".</div>
                </div>
                '''),
            textwrap.dedent( # step 12
                f'''
                We've reached the end of the first steps wizard. Here are some links you can follow to deepen your understanding of Cloudomation:

                - Learn more about using Cloudomation in the [Tutorial](https://cloudomation.com/documentation/tutorial/){{ext}}
                - [Invite users](/users){{ext}} to join your Cloudomation client "{client_name}"
                - Set up [integration with Git](https://cloudomation.com/documentation/using-flow-scripts-from-git/){{ext}}
                - Read the flow [script function reference](/documentation/Flow%20script%20function%20reference){{ext}}
                - Explore available [task types](/documentation/Tasks){{ext}}
                - Set up [webhooks](https://cloudomation.com/documentation/webhooks/){{ext}}.
                - If there are any questions or issues, please do not hesitate to [contact us](/contact){{ext}}.

                Enjoy automating!
                '''),
        ]

        return messages[step-1]

    for step in range(1, number_of_steps+1):
        m = system.message(
            subject=f'Step {step} of {number_of_steps}',
            message_type='POPUP',
            body=
            {
                'type':'object',
                'properties': {                
                    'content': {
                        'element': 'markdown',
                        'description': get_message(step),
                        'order': 1,
                    },
                    'acknowledged': {
                        'label':'OK',
                        'element': 'submit',
                        'type': 'boolean',
                        'order': 2,
                    },
                },
                'required': [
                    'acknowledged',
                ],        
            }
        )

        m.wait()
        dt_now = datetime.datetime.now(tz=datetime.timezone.utc)
        
        if step == 2:
            start_time = time.time()
            flow = None
            while flow is None and time.time() < start_time + time_out:
                for cur_flow in system.flows():
                    try:
                        if cur_flow.get('created_at') is not None and datetime.datetime.strptime(cur_flow.get('created_at'), DT_FORMAT) > dt_now:
                            flow = cur_flow
                            break
                    except Exception:
                        pass
                this.sleep(poll_interval)

        elif step == 3 or step == 6:
            start_time = time.time()
            execution = None
            while execution is None and time.time() < start_time + time_out:
                for cur_execution in system.executions():
                    try:
                        if cur_execution.get('created_at') is not None and datetime.datetime.strptime(cur_execution.get('created_at'), DT_FORMAT) > dt_now:
                            execution = cur_execution
                            break
                    except Exception:
                        pass
                this.sleep(poll_interval)
            if step == 3:
                execution.wait()
                execution_name, execution_status, output_value = execution.load('name', 'status', 'output_value')
                output_value_str = yaml.safe_dump(output_value, default_flow_style=False)
            else:
                execution_name = execution.load('name')
        
        elif step == 4:
            start_time = time.time()
            setting = None
            while setting is None and time.time() < start_time + time_out:
                for cur_setting in system.settings():
                    try:
                        if cur_setting is not None and cur_setting.get('created_at') is not None and datetime.datetime.strptime(cur_setting.get('created_at'), DT_FORMAT) > dt_now:
                            setting = cur_setting
                            break
                    except Exception:
                        pass
                this.sleep(poll_interval)
            setting_id = setting.get('id')

        elif step == 5:
            start_time = time.time()
            before_modified_at = setting.load('modified_at')
            while time.time() < start_time + time_out:
                setting = None
                for cur_setting in system.settings():
                    try:
                        if cur_setting is not None and cur_setting.load('modified_at') > before_modified_at:
                            setting = cur_setting
                            break
                    except Exception:
                        pass
                if setting is None:
                    continue
                modified_at = setting.load('modified_at')
                if modified_at is not None and modified_at > before_modified_at:
                    before_modified_at = modified_at
                    value = setting.get('value')
                    if all(k in value for k in ('text', 'iterations', 'delay')):
                        break
                    else:
                        check_m = system.message(
                            subject=f'Please check - Step {step} of {number_of_steps}',
                            message_type='POPUP',
                            body=
                            {
                                'type':'object',
                                'properties': {                
                                    'content': {
                                        'element': 'markdown',
                                        'description': textwrap.dedent(
                                                            f'''
                                                            Please make sure that the setting contains all the keys:

                                                            - text
                                                            - iterations
                                                            - delay

                                                            Like in this example:

                                                            ```yaml
                                                            text: Hello {user_name}!
                                                            iterations: 10
                                                            delay: 6
                                                            ```

                                                            The values of the keys will be used in the next step.
                                                            '''),
                                        'order': 1,
                                    },
                                    'acknowledged': {
                                        'label':'OK',
                                        'element': 'submit',
                                        'type': 'boolean',
                                        'order': 2,
                                    },
                                },
                                'required': [
                                    'acknowledged',
                                ],        
                            }
                        )
                        check_m.wait()
                        continue
                this.sleep(poll_interval)
            setting_name, setting_value = setting.load('name', 'value')
            text = setting_value['text']
            iterations = setting_value['iterations']
            delay = setting_value['delay']
        elif step == 7:
            start_time = time.time()
            while time.time() < start_time + time_out:
                if execution.load('status') in ('PAUSED', 'ENDED_SUCCESS', 'ENDED_ERROR', 'ENDED_CANCELLED'):
                    break
                this.sleep(poll_interval)
        elif step == 9:
            start_time = time.time()
            file_content = None
            execution = None
            while time.time() < start_time + time_out:
                if file_content is None:
                    for cur_files in system.files():
                        try:
                            if cur_files.load('name') == 'myfile.txt':
                                myfile = system.file('myfile.txt')
                                file_content = myfile.get('content')
                        except Exception:
                            pass
                if execution is None:
                    for cur_execution in system.executions():
                        try:
                            if cur_execution.get('created_at') is not None and datetime.datetime.strptime(cur_execution.get('created_at'), DT_FORMAT) > dt_now:
                                execution = cur_execution
                        except Exception:
                            pass
                if file_content and execution:
                    break
                this.sleep(poll_interval) 
            execution_name = execution.load('name')
        elif step == 10:
            start_time = time.time()
            task = None
            execution = None
            while time.time() < start_time + time_out:
                for cur_execution in system.executions():
                    try:
                        created_at = cur_execution.get('created_at')
                        if created_at is not None and datetime.datetime.strptime(created_at, DT_FORMAT) > dt_now:
                            if cur_execution.get('type') == 'TASK':
                                task = cur_execution
                            else:
                                execution = cur_execution
                    except Exception:
                        pass
                if task and execution:
                    break
                this.sleep(poll_interval)
            execution.wait(return_when=system.return_when.ALL_SUCCEEDED)
            execution_name = execution.load('name')
            message = unescape(task.get('output_value')['json']['value']['joke'])
    
    return this.success('all done')