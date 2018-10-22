"""
This flow script shows how the REST and INPUT tasks can be used together, by
requesting parameters for a REST API call from a user.
In this small example, a user is asked for a country name. The flow script then
queries the REST API of the geonames service, which provides information about
countries. The information about the country is then returned to the user, and
the user is asked if they liked the information. Their response is captured in
the end message of the flow script.

This flow script call the geonames REST API to get information about a country.
In order to use the geonames REST API, it is necessary to create a geonames
account and enable it for the use of their webservices. They are free, but
there are usage limits (very generous ones). If you are interested in using the
geonames web services, you can register here: http://www.geonames.org/login and
use your own account to execute this flow script. If not, we will use the demo
user name provided by geonames for demo purposes only. Since this demo account
also has usage limits, there is a chance that the flow script will fail due to
these limits.
"""

# (1) define handler function for the Cloudomation class (c)
def handler(c):

# (2) use settings
    """
    To use the geonames REST API, it is required to register an application,
    which is identified via a user name that has to be provided with every
    REST call. The best way to manage parameters like this is to store them
    as Cloudomation settings. In this way, usernames can be changed easily in
    the settings view without having to edit the flow scripts which use it.
    For this example flow script, we will first check if the setting exists
    and if it doesn't, we will create it and fill it with a demo user name.
    This is not recommended best practice - the user name should not be hard
    coded into the flow script. Another option would be to check if the
    setting exists and if not, as the user to input a user name. However for
    the purposes of this example flow script, we will create a setting that
    contains the user name to demonstate how to use settings.
    NOTE that settings are not intended for passwords or other sensible
    information. For passwords, we recommend the use of Hashicorp Vault.
    """

    # we check if there is a setting with the key geonames_username
    if c.setting('geonames_username') is None:
        # if the setting doesn't exist, we set it to the demo user name.
        # if it does exist, this line will be skipped.
        c.setting('geonames_username', 'demo')

    # then we read out the value of the geonames_username setting
    # note that this is not related to the previous check. We need to read
    # the setting in any case, independent of whether it was set by the script,
    # or before the script was run
    username = c.setting('geonames_username')

# (3) use INPUT task
    # We want to provide the user with information about a country. We ask for
    # a country and explain what we are planning to do.
    countryname_request = c.task(
        'INPUT',
         # the INPUT function has one required parameter: the request. This is
         # what users will see and respond to.
        request=(
            'This is a country information service. If you input a country '
            'name, I will tell you a few things about this country. Please '
            'only type one country at a time. Which country would you like '
            'to learn about?'
        )
    # after defining the INPUT task, we directly execute it with .run()
    ).run()
    # now, the variable countryname_request contains the *execution object*
    # of the input task. From the execution object, we can get e.g. its ID,
    # its status, its runtime etc. - and most importantly, its outputs.
    # What kind of outputs you can get from an execution object depends on
    # the execution, i.e. which task you ran.

    # we get the outputs and store them in a variable 'countryname_results'
    countryname_result = countryname_request.getOutputs()

    # because we want to learn about the INPUT task, we log all the outputs to
    # see what we get back. This is not required, we do this just for learning
    # purposes. Take a look at the log to see what the INPUT task returns.
    c.logln(countryname_result)

    # It returns a JSON element and we can access the individual elements with
    # standard Python syntax: we are only interested in the user's response,
    # which should be a country name. We store it in the variable 'countryname'.
    countryname = countryname_result['response']

# (4) use REST task
    """
    Now, we want to get some information about the country. To request
    formation about a country, the geonames API requires the ISO-2 country code
    of that country, so our first request will be to get the ISO-2 country code
    for the country name. This is also an opportunity for us to see if the user
    input a valid country name - if they didn't, this request will fail.
    """

    # Here, we use the two previously defined paramenters: the username we read
    # from a setting, and the country name from the user input. Then we execute
    # the REST task with .run(). Note that your can use standard python string
    # formatting functionality for defining the URL with parameters.
    countrycode_request = c.task(
        'REST',
        url = f'http://api.geonames.org/search?name={
            countryname
        }&featureCode=PCLI&type=JSON&username={
            username
        }').run()
    # again, we execute the REST task right away and store the resulting
    # execution object in a variable: countrycode_request

    # now we get the response returned from the REST call
    countrycode_response = countrycode_request.getOutputs()

    # First, we need to check if the REST call returned anything. If it didn't,
    # we will end the execution and inform the user. If it did, we will continue.

    # the geonames call returns the number of search results, which we access:
    response_count = countrycode_response['json']['totalResultsCount']

    # check if the REST call returned 0 results
    if response_count < 1:
        # if it is 0, we will end the execution and tell the user that we
        # coudn't find the country. If the REST call did return a result,
        # this line will be skipped and the script will continue.
        return c.end(
            'error',
            message='We could not find the country you named.'
        )

    # because we want to learn about the REST task, we log the response
    # returned by the REST call. Note that here, we use c.logln, which appends
    # a new line to the log. You could use c.log as well, which would append a
    # string - doesn't look as nice, though, se we use c.logln to log our
    # results in a new line. Take a look at the log to see what is returend by
    # the REST call. It is again a JSON whose elements we can access.
    c.logln(countrycode_response)

    # we access the country code. If you look at the response which we logged,
    # you will see that the JSON is nested so we need to go through a few
    # layers before we get to the country code.
    countrycode = countrycode_response['json']['geonames'][0]['countryCode']

# (5) another REST task
    # now that we have the country code, we want to get some information
    # about the country
    countryinfo_request = c.task(
        'REST',
        url = f'http://api.geonames.org/countryInfo?country={
            countrycode
        }&type=JSON&username={
            username
        }').run()

    # we get the ouput from the execution object
    countryinfo_result = countryinfo_request.getOutputs()['json']['geonames'][0]

# (6) give the user some information about the country and ask for  feedback
    # now that we already saw how the INPUT task works, we chain it all
    # together, directly getting the output and not storing the execution
    # object in a separate variable.
    user_feedback = c.task(
        'INPUT',
        request=(f'Here is some information about {
                countryname
            }. It is located in {
                countryinfo_result['continentName']
            }, its capital is {
                countryinfo_result['capital']
            }, it has a population of {
                countryinfo_result['population']
            }, and an area of {
                countryinfo_result['areaInSqKm']
            } square kilometers. Did you like this information?'
        ).run(
    ).getOutputs()['response']

# (7) end execution
    # we add the user feedback to the end message
    c.end(
        'success',
        message=f'Country info provided. Did the user like the information? {
            user_feedback
        }'
    )
