import textwrap
import time
import yaml


def handler(system, this):
    user_name, client_name = this.get('user_name', 'client_name')
    user_name = user_name[0].upper() + user_name[1:]
    step = 1
    number_of_steps = 12
    m = system.message(
        type='popup',
        subject='First steps',
        message=textwrap.dedent(
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
    )
    while True:
        if m.load('acknowledged') == 'True':
            break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
    )
    now = time.time()
    flow = None
    while flow is None:
        for cur_flow in system.flows():
            if cur_flow.get('created_at') is not None and cur_flow.get('created_at') > now:
                flow = cur_flow
                break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
            f'''
            A flow contains the automation logic which is processed by Cloudomation when the flow is run.

            You can learn more about flows in the [Flows](/documentation/Flows){{ext}} documentation.

            The newly created flow is opened for you.
            You can see all opened flow records below the <strong><i class="fa fa-code"></i> Flows</strong> resource in the menu on the left.

            Flows contain two important fields:
            - The flow name
            - The flow script

            Flow names must be unique among all flows.

            The flow script should be python code with a handler function.
            There are many python tutorials out there, for example [The Python Tutorial](https://docs.python.org/3/tutorial/){{ext}} by the Python Software Foundation

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
    )
    now = time.time()
    execution = None
    while execution is None:
        for cur_execution in system.executions():
            if cur_execution.get('creation_time') is not None and cur_execution.get('creation_time') > now:
                execution = cur_execution
                break
        this.sleep(1)
    execution.wait()
    execution_name, execution_status, output_value = execution.load('name', 'status', 'output_value')
    output_value_str = yaml.safe_dump(output_value, default_flow_style=False)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
            f'''
            **Congratulations!**

            Your execution `{execution_name}` just ended with status `{execution_status}`.

            When you pressed <span class="text-success"><i class="fa fa-play"></i> Try</span>, the user-interface switched to the newly created execution record.
            You can see details about the execution in the execution record.
            When you scroll down, you will see the "Outputs" field which contains:

            ```yaml
{textwrap.indent(output_value_str, '            ')}
            ```

            ---

            Next, let's look at the <strong><i class="fa fa-sliders"></i> Settings</strong> resource.

            <div class="alert alert-primary">
                <strong class="d-block pb-1">Your tasks:</strong>
                <div><i class="fa fa-check-square-o"></i> Select the <strong><i class="fa fa-sliders"></i> Settings</strong> resource.</div>
                <div><i class="fa fa-check-square-o"></i> Create a new setting by pressing <span class="text-primary"><i class="fa fa-file-o"></i> New</span> in the action bar.</div>
            </div>
            '''),
    )
    now = time.time()
    setting = None
    while setting is None:
        for cur_setting in system.settings():
            if cur_setting.get('created_at') is not None and cur_setting.get('created_at') > now:
                setting = cur_setting
                break
        this.sleep(1)
    setting_id = setting.get('id')
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
    )
    before_modified_at = setting.load('modified_at')
    # this.log(before_modified_at=before_modified_at)
    while True:
        setting = None
        for cur_setting in system.settings():
            if cur_setting.get('id') == setting_id:
                setting = cur_setting
                break
        if setting is None:
            continue
        modified_at = setting.load('modified_at')
        # this.log(before_modified_at=before_modified_at, modified_at=modified_at)
        if modified_at is not None and modified_at > before_modified_at:
            before_modified_at = modified_at
            value = setting.load('value')
            # this.log(value=value)
            if value == 'setting value':
                continue
            if all(k in value for k in ('text', 'iterations', 'delay')):
                break
            m = system.message(
                type='popup',
                subject=f'Step {step} of {number_of_steps}',
                message=textwrap.dedent(
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
            )
        this.sleep(1)
    setting_name, setting_value = setting.load('name', 'value')
    text = setting_value['text']
    iterations = setting_value['iterations']
    delay = setting_value['delay']
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
    )
    execution = None
    while execution is None:
        for cur_execution in system.executions():
            if cur_execution.get('creation_time') is not None and cur_execution.get('creation_time') > now:
                execution = cur_execution
                break
        this.sleep(1)
    execution_name = execution.load('name')
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
    )
    while True:
        if execution.load('status') in ('paused', 'success', 'error', 'cancelled'):
            break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
    )
    while True:
        if m.load('acknowledged') == 'True':
            break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
            f'''
            Now, let's see some configuration options.

            Settings can also be used to tweak the behaviour of Cloudomation.

            **Execution expiry**

            You might have already noticed that execution records expire.
            You can see the expiration time in the fields of an ended execution record.
            Per default, once an execution reaches and end state (success or error), it will be kept available for one week.
            Once this time passed, the execution record is removed automatically.

            This can be changed by creating a setting called `client.execution.retention_time.minutes`.
            The value of this setting is used as the retention time for all new executions.

            <div class="alert alert-primary">
                <strong class="d-block pb-1">Your tasks:</strong>
                <div><i class="fa fa-check-square-o"></i> Create a setting and change the name to <code>client.execution.retention_time.minutes</code>.</div>
                <div><i class="fa fa-check-square-o"></i> Change the value of the setting to <code>10</code>.</div>
                <div><i class="fa fa-check-square-o"></i> Save the setting by pressing <span class="text-primary"><i class="fa fa-save"></i> Save</span> in the action bar.</div>
            </div>
            '''),
    )
    now = time.time()
    setting = None
    while setting is None:
        for cur_setting in system.settings():
            if cur_setting.load('name') == 'client.execution.retention_time.minutes':
                setting = cur_setting
                break
        this.sleep(1)
    while True:
        retention_time = setting.load('value')
        if type(retention_time) == int:
            break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
            f'''
            Now all new executions will expire {retention_time} minutes after they reach an end state.

            You can learn more about configuration options in the [Settings](/documentation/Settings#clientconfiguration){{ext}} documentation.

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
                return this.end('success', message=joke)</code></pre>
                </div>
                <div><i class="fa fa-check-square-o"></i> Create an execution of the flow by pressing <span class="text-success"><i class="fa fa-play"></i> Try</span> in the action bar.</div>
            </div>
            '''),
    )
    execution = None
    while execution is None:
        for cur_execution in system.executions():
            if cur_execution.get('creation_time') is not None and cur_execution.get('creation_time') > now and cur_execution.get('type') == 'flow':
                execution = cur_execution
                break
        this.sleep(1)
    execution.wait(return_when=system.return_when.ALL_ENDED)
    execution_name, message = execution.load('name', 'message')
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
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
                <strong class="d-block pb-1">Your first task:</strong>
                <div><i class="fa fa-check-square-o"></i> Close this message by pressing "OK".</div>
            </div>
            '''),
    )
    while True:
        if m.load('acknowledged') == 'True':
            break
        this.sleep(1)
    step += 1

    m = system.message(
        type='popup',
        subject=f'Step {step} of {number_of_steps}',
        message=textwrap.dedent(
            f'''
            We've reached the end of the first steps wizard. Here are some links you can follow to deepen your understanding of Cloudomation:

            - [Invite users](/users){{ext}} to join your Cloudomation client "{client_name}"
            - Set up [integration with Git](/documentation/Using%20flow%20scripts%20from%20git){{ext}}
            - Read the flow [script function reference](/documentation/Flow%20script%20function%20reference){{ext}}
            - Explore available [task types](/documentation/Tasks){{ext}}
            - Set up [webhooks](/documentation/Webhooks){{ext}}.
            - If there are any questions or issues, please do not hesitate to [contact us](/contact){{ext}}.

            Enjoy automating!
            '''),
    )
    return this.success('all done')
