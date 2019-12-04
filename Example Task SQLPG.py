def handler(system, this):
    postgres_server_version = this.task(
        'SQLPS',
        host='my-postgres-server',
        fetchval='SELECT version()',
    ).get('output_value')['result']
    this.log(postgres_server_version=postgres_server_version)
    return this.success('all done')
