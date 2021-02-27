import base64
import hashlib
import hmac
from urllib.parse import quote, urlencode


"""
Adds the signature bit and produces a encoded query string fpr Apache Cloud Stack API

inputs:
    - command:
        type: dict
        required: True
        doc: dict which contains the acutal command and the apikey e.g.: { 'command': 'deployVirtualMachine', 'apikey': 'your-api-key' }
    - secret:
        type: string
        required: True
        doc: the api secret
outputs:
    - query_str:
        type: str
        doc: the encoded query string for the api call to apache cloud stack
"""

import flow_api

def handler(system: flow_api.System, this: flow_api.Execution):
    # retrieve the necessary inputs and store them in local variables
    data = this.get('input_value')
    command = data.get('command')
    secret = data.get('secret')

    # order matters
    arguments = sorted(command.items())

    # urllib.parse.urlencode is not good enough here.
    # key contains should only contain safe content already.
    # safe="*" is required when producing the signature.
    query_string = "&".join("=".join((key, quote(value, safe="*")))
                          for key, value in arguments)

    # Signing using HMAC-SHA1
    digest = hmac.new(
        secret.encode("utf-8"),
        msg=query_string.lower().encode("utf-8"),
        digestmod=hashlib.sha1).digest()

    # encode the signature 
    signature = base64.b64encode(digest).decode("utf-8")
    params = dict(command, signature=signature)

    # urlencode the query string
    query_str = urlencode(params)

    # save the query string in the outputs
    this.save(output_value={'query_str': query_str})
    return this.success('all done')