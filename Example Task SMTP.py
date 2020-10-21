def handler(system, this):
    # create an SMPT task and run it
    this.task(
        'SMTP',
        inputs={
                'from': 'Cloudomation <info@cloudomation.com>',
                'to': 'info@cloudomation.com',
                'subject': 'Cloudomation email',
                # the text will be the email body. Alternatively you could add
                # a html formatted body with the key 'html'.
                'text': 'This email was sent with Cloudomation',
                'login': 'cloudomation@cloudomation.com',
                'password': '****',
                'smtp_host': 'SMTP.example.com',
                'smtp_port': 587,
                'use_tls': True
        }
    )
    # there are no outputs for the SMTP task
    this.success(message='all done')
