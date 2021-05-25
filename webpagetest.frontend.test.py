
import time
import json

import flow_api

'''
Frontend testing with Webpagetest
Parameters for the test are in the setting 'webpagetest'.
Example setting:
url_list:
  - url: 'https://www.pexels.com/search/cat/'
  - url: 'https://europa.eu/european-union/index_en'    
  - url: 'https://www.nytimes.com/'
test_params:
  f: json
  runs: '3'
  video: '0'
  private: '1'
  location: 'Test:Firefox'
  priority: '6'

Results are saved unter Workspace->Files 'webpagetest.result.x.json'
The server for the tests will be created before the test and destroyed afterwards
Inputs:
    gcloud_connection: <string> name of the connection stored in the cloudomation workspace
'''

def handler(system: flow_api.System, this: flow_api.Execution):
    start_time = time.time()
    inputs = this.get('input_value')
    gcloud_connection = inputs.get('gcloud_connection')
    task = this.flow('webpagetest.create.server', gcloud_connection=gcloud_connection)
    output = task.get('output_value')
    wait = output.get('wait')
    if wait:
        this.sleep(180)  # wait until the server is configured
    error = None
    
    options = system.setting('webpagetest').get('value')
    webpagetest_server = system.setting('webpagetestserver').get('value')
    url_list = options.get('url_list', [])
    test_params = options.get('test_params', {})
    host = webpagetest_server.get('hostname')

    test_ids = {}
    for url in url_list:
        test_params['url'] = url.get('url')
        this.log(f'building test_params {url}')
        result = this.task(
            'REST',
            url=f'http://{host}:4000/runtest.php',
            urlencoded=test_params,
            name=f'Frontend Performance test {url.get("url")}',
        ).get('output_value')['json']
        test_ids[url.get('url')] = {
            'id': result.get('data').get('testId'), 
            'jsonUrl': result.get('data').get('jsonUrl'), 
            'running': True,
        }
    
    tests_completed = False
    while not tests_completed:
        this.sleep(240)
        for i in test_ids.keys():
            check_running = this.task(
                'REST',
                url=f'http://{host}:4000/testStatus.php',
                urlencoded={'f':'json', 'test': test_ids[i].get('id')},
                name=f'check test status for {i}',
            ).get('output_value')['json']
            test_ids[i]['running'] = check_running.get('data').get('statusCode') != 200        
        for i in test_ids.keys():
            if test_ids[i]['running']:
                break
        else:
            tests_completed=True

    test_results = {}
    for i in test_ids.keys():
        test_results[i] = {
            'info':'Data extracted from webpagetest jsonResult data->median',
            'resultUrl': f'http://{host}:4000/result/{test_ids[i].get("id")}',
            'test_runs': test_params.get('runs'),
            'firstView':{}, 
            'repeatView':{},
        }
        test_result = this.task(
            'REST',
            url=f'http://{host}:4000/jsonResult.php',
            urlencoded={
                'test':test_ids[i].get("id"),
                'requests':'0',
                'pagespeed':'1',
                'domains':'0',
                'breakdown':'0'
            },
            name=f'get test result for {i}',
        ).get('output_value')['json']
        median = test_result.get('data').get('median')
        if not median:
            return this.error('Webpagetest failed')
        fv = median.get('firstView')
        rv = median.get('repeatView')
        test_results[i]['timestamp_test_completed'] = test_result.get('data').get('completed')
        test_results[i]['firstView']['domComplete'] = fv.get('domComplete')
        test_results[i]['firstView']['fullyLoaded'] = fv.get('fullyLoaded')
        test_results[i]['firstView']['fullyLoadedCPUms'] = fv.get('fullyLoadedCPUms')
        test_results[i]['firstView']['browser_name'] = fv.get('browser_name')
        test_results[i]['repeatView']['domComplete'] = rv.get('domComplete')
        test_results[i]['repeatView']['fullyLoaded'] = rv.get('fullyLoaded')
        test_results[i]['repeatView']['fullyLoadedCPUms'] = rv.get('fullyLoadedCPUms')
        test_results[i]['repeatView']['browser_name'] = rv.get('browser_name')
    x = 0
    while system.file(f'webpagetest.result.{x}.json').exists():
        x = x + 1
    new_file = system.file(f'webpagetest.result.{x}.json')
    new_file.save(text=json.dumps(test_results, indent=4))
    

    this.flow('webpagetest.remove.server', wait=False)
    
    if error:
        return this.error(error)
    t = time.time() - start_time
    return this.success(f'all done after {int(t)} sec')
