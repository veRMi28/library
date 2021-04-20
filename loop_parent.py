# This flow script exemplifies the usage of a for-loop to execute several REST
# API calls. The calls loop through a list of input variables that are defined
# in a setting. The calls are defined in a separate flow script that is called
# from this parent flow script. This enables faster parallel processing of the
# REST calls, and showcases the interaction between flow scripts.

# In this example, we use the goenames REST API, which you might know from
# other examples already. We will loop through a list of countries that are
# provided in a setting. The geonames API doesn't allow bulk requests, so calls
# can only ever request information about one single country.
# Other useful applications of such loops could be to copy data from and to
# different systems, install components on different servers, run a set of test
# cases etc.

# A note on the limitations of for loops: they only comfortably allow to loop
# through a list of one single parameter. The cloudomation clone execution
# function enables the handling of more advanced situations in which several
# parameters have to be changed, and/or different parameters are kept and
# changed for different runs of an execution. The clone function allows for
# "templating" of executions that can then be called again with different
# parameters. Look for the clone example for details.
# Another limitation of loops is that you have to be careful with exception
# handling. If you loop through a list and you have a typo in one value, it
# will crash and not process the rest of the list, unless you handle this
# properly (as showcased in this example).

# (1) Define handler function which receives the Cloudomation System
# object (system) and an Execution object of this execution (this)
import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):

# (2) Create a setting with country names
    # In a real-life application of this functionality, this setting would
    # probably be created by another flow script, or be defined manually once.
    # First, we check if the setting already exists. If it doesn't, we create
    # it. Feel free to change the selection of countries.
    # Note that we create a setting that contains a list. Settings can contain
    # any object that can be serialised into a yaml - lists, json etc.

    geonames_countrynames = system.setting('geonames_countrynames')
    if not geonames_countrynames.exists():
        geonames_countrynames.save(value=["Austria", "Latvia", "Azerbaijan"])

    countrynames = geonames_countrynames.get('value')

# (3) Loop through the countries
    # In order to get the information we want, we need to do several API calls.
    # To speed this up, we parallelise the API calls by executing them in a
    # separate flow script, which we start as child executions.

    # We create an empty list to which we will append our child execution
    # objects in the for loop.
    calls = []

    # We create a separate empty list to which we will append inputs that are
    # not valid countries.
    invalids = []

    for countryname in countrynames:
        # We call the flow script that contains the REST calls with the c.flow
        # function. We store the execution object returned by the c.flow
        # function in the call variable.
        call = this.flow(
            'loop_child',
            # I can add any number of parameters here. As long as they are not
            # called the same as the defined parameters for the flow function,
            # the are appended to the input dictionary that is passed to the
            # child execution.
            # In this example, the child execution will be passed a key-value
            # pair with countryname as the key, and the first value in the
            # countryname setting as the value.
            # If I added another argument weather = nice, a second key-value
            # pair would be added to the input dictionary for the child
            # execution, with the key weather and the value nice.
            # Note that I can also pass the same input as a dictionary with the
            # inputs parameter. The below line is equivalent to
            # input_value = { 'countryname': countryname }
            countryname = countryname,
            run=False,
        # run_async() starts the child execution and then immediately returns.
        # This means that the for loop continues and the next child execution
        # is started right away - the REST calls will be executed in parallel.
        ).run_async()
        # All execution objects are appended to the calls list.
        calls.append(call)

# (4) Wait for all child executions to finish

    # Here, I tell the flow script to wait for all elements in the calls list
    # to finish before it continues. Remember that the calls list contains all
    # execution objects that we started in the for loop.
    this.wait_for(*calls)

# (5) Get outputs of child executions, and set outputs of parent execution

    # Now, we take all the execution objects and get their outputs. Depending
    # on whether or not there was an error, we treat the results differently.
    for call in calls:
        # Get all outputs from all child executions
        result = call.load('output_value')
        # If there was an error, append the output of the erroneous execution
        # to our list of invalid country names.
        if 'error' in result:
            invalids.append(result['error'])
        # If there was no error, we directly set the output of the flow script
        # to the output of the child executions.
        else:
            this.log(result)

    # The errors need a bit more processing: here, we set an output that
    # contains the key "warning", information about the number of failed calls,
    # and the country names for which there was an error.
    if len(invalids) > 0:
        this.log(
            f'warning: no information was found for {len(invalids)} countries'
        )
        this.log(invalid_countries=invalids)

# (6) Once we're done we end the execution.
    return this.success(message='all done')
