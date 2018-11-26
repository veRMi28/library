'''
This flow script is called by the loop_parent.py flow script. It executes a
number of REST calls to the geonames API. You cannot execute this flow script
as it is on its own, as it requires inputs that are passed on from the parent
flow.
In this example, we are interested in the coordinates of each country's
capital city.
Due to the structure of the API calls available in the geonames API, we
have several steps to complete: starting with the country name (which is
our input), we need to get the country code, then the capital's name, and
then the capital's coordinates.
Here, we can begin to see why looping is useful: even for fairly simple
REST calls, it is often necessary to chain together several calls to get
the information you need, so writing a loop can save a lot of lines in your
script - and parallelising the calls can save you a lot of time.
Note that after the first API call, we add a check if there was a valid
result and set the result to a warning if there isn't. This is to make
sure that the loop runs through all input values even if there are invalid
values in the input list.
Exception handling depends on the API: the geonames API simply returns an
empty object for invalid search queries like the ones we are executing,
with a success status code. For other errors in the call (e.g. missing
parameters) it would return a status code that you could use to catch
exceptions. In our case, we assume that we need to ensure that errors in
the input list don't trip up the loop, but assume that other parameters
are correct, such as the username and the call syntax. Assuming that this
runs automatically, the input list is the only thing that will change from
run to run so it is the most likely source of errors.
'''

# (1) Define handler function for the Cloudomation class (c)
def handler(c):

# (2) Set username for geonames API
    if not c.setting('geonames_username'):
        c.setting('geonames_username', 'demo')

    username = c.setting('geonames_username')

# (3) get inputs from parent execution
    # The parent execution passed inputs to this execution, therefore we
    # don't need to specify an execution ID from which to get the inputs.
    # c.getInputs() will capture the inputs given by the parent execution.
    countryname = c.getInputs()['countryname']

# (4) call the geonames API

    countrycode_response = c.task(
        'REST',
        url=(f'http://api.geonames.org/search?'
             f'name={countryname}&'
             f'featureCode=PCLI'
             f'&type=JSON'
             f'&username={username}')
    ).run(
    ).getOutputs(
    )['json']['geonames']

    # Check if the result contains something
    if not countrycode_response:
        # If it doesn't, we set the output to error and send back the
        # invalid country name
        c.setOutput('error', countryname)

    else:
        # If there is a valid response, we continue with the API calls
        countrycode = countrycode_response[0]['countryCode']
        capitalname = c.task(
            'REST',
            url=(f'http://api.geonames.org/countryInfo?'
                 f'country={countrycode}'
                 f'&type=JSON'
                 f'&username={username}')
        ).run(
        ).getOutputs(
        )['json']['geonames'][0]['capital']

        capitalcoordinates_response = c.task(
            'REST',
            url=(f'http://api.geonames.org/search?'
                 f'name={capitalname}&'
                 f'featureCode=PPLC'
                 f'&type=JSON'
                 f'&username={username}')
        ).run(
        ).getOutputs(
        )['json']['geonames'][0]

        # The coordinates are two values. To access them by key in the json
        # which is returned by the geonames API, we need to loop through
        # the result.
        capitalcoordinates = {
            k: float(v)
            for k, v
            in capitalcoordinates_response.items()
            if k
            in ('lat', 'lng')
        }

# (5) Set outputs
        c.setOutput(capitalname, capitalcoordinates)

# (6) Once we're done we end the execution.
    c.success(message='all done')
