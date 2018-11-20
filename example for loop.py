'''
This flow script exemplifies the usage of a for-loop to execute several REST
API calls. The calls loop through a list of input variables that are defined
in a setting.
It shows how Cloudomation functionality can be used jointly with standard
Python funcions such as for loops to create efficient automations that benefit
from Cloudomation functionality such as transaction safety, consistent logging,
and scalability.
In this example, we use the goenames REST API, which you might know from other
examples already. We will lopp through a list of countries that are provided
in a setting. The geonames API doesn't allow bulk requests, so calls can only
ever request information about one single country.
Other useful applications of such loops could be to copy data from and to
different systems, install components on different servers, run a set of test
cases etc.
A note on the limitations of for loops: they only comfortably allow to loop
through a list of one single parameter. The cloudomation clone execution
function enables the handling of more advanced situations in which several
parameters have to be changed, and/or different parameters are kept and changed
for different runs of an execution. The clone function allows for "templating"
of executions that can then be called again with different parameters.
Look for the clone example for details.
Another limitation of loops is that you have to be careful with exception
handling. If you loop through a list and you have a typo in one value, it will
crash and not process the rest of the list, unless you handle this properly
(as showcased in this example).
'''

# (1) Define handler function for the Cloudomation class (c)
def handler(c):

# (2) Set username for geonames API
    if not c.setting('geonames_username'):
        c.setting('geonames_username', 'demo')

    username = c.setting('geonames_username')

# (3) Create a setting with country names
    '''
    In a real-life application of this functionality, this setting would
    probably be created by another flow script, or be defined manually once.
    We check if the setting already exists. If it doesn't, we create it.
    Feel free to change the selection of countries.
    Note that we create a setting that contains a list. Settings can contain
    any object that can be serialised into a yaml - lists, json etc.
    '''
    if not c.setting('geonames_countrynames'):
        c.setting(
            'geonames_countrynames',
            ["Austria", "Latvia", "Azerbaijan"]
        )

    countrynames = c.setting('geonames_countrynames')

# (4) Loop through API calls
    '''
    In this example, we are interested in the coordinates of each country's
    capital city.
    Due to the structure of the API calls available in the geonames API, we
    have several steps to complete: starting with the country name (which is
    our input), we need to get the country code, then the capital's name, and
    then the capital's coordinates.
    Here, we can begin to see why lopping is useful: even for fairly simple
    REST calls, it is often necessary to chain together several calls to get
    the information you need, so writing a loop can save a lot of lines in your
    script.
    Note that in between each API call, we add a check if there was a valid
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

    for countryname in countrynames:
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

        # check if the result contains something
        if not countrycode_response:
            capitalname = 'warning'
            capitalcoordinates = f'country {countryname} not found!'

        else:
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
            capitalcoordinates = [
                capitalcoordinates_response[i] for i in ['lat', 'lng']
            ]

# (5) Set outputs - this is still part of the for loop, so the results for
# each country are appended to the output.
        c.setOutput(capitalname, capitalcoordinates, append=True)

# (6) Once we're done we end the execution.
    c.success(message='all done')
