def handler(system, this):
    # create an SMPT task and run it
    this.task(
        'SMTP',
        inputs={
                'from': 'cloudomation@cloudomation.io',
                'to': 'info@cloudomation.io',
                'subject': 'Cloudomation email',
                # the text will be the email body. Alternatively you could add
                # a html formatted body with the key 'html'.
                'text': 'This email was sent with Cloudomation',
                'login': 'cloudomation@cloudomation.io',
                'password': '****',
                'smtp_host': 'SMTP.example.com',
                'smtp_port': 587,
                'use_tls': True
        }
    ).run()
    # there are no outputs for the SMTP task
    this.success(message='all done')
