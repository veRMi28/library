"""
todo.py - a simple TODO app based on a Cloudomation webhook
"""

import uuid
import pystache
import flow_api


MAIN = '''
<html>
<head>
    <title>Cloudomation TODO</title>
    <style>
    body {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    button {
        cursor: pointer;
        font-size: 20px;
    }
    input {
        font-size: 20px;
        padding: 0 10px;
    }
    .todo-list {
        display: flex;
        flex-direction: column;
        width: 500px;
        border: 1px solid lightgray;
        border-radius: 8px;
        background: lightyellow;
    }
    .todo-new {
        padding: 10px;
        display: flex;
        justify-content: space-between;
    }
    .todo-item {
        padding: 10px;
        border-top: 1px dashed gray;
        display: flex;
        justify-content: space-between;
    }
    .todo-label {
        border: 0;
        background-color: transparent;
    }
    .todo-label-done {
        text-decoration: line-through;
    }
    </style>
</head>
<body>
    <h1>Cloudomation TODO app</h1>
    {{#debug}}
    <pre>
method: {{method}}
json: {{json}}
path: {{path}}
query: {{query}}
    </pre>
    {{/debug}}
    <form class="todo-list" method="post">
        <div class="todo-new"><input type="text" name="todo-new" placeholder="What needs to be done?" />&nbsp;<button name="todo-new" type="submit">add</button></div>
        {{#todos}}
        <div class="todo-item">
            {{^done}}
            <button class="todo-label todo-label-todo" name="todo-done" value="{{id}}" type="submit">&#x2610; {{label}}</button>
            {{/done}}
            {{#done}}
            <button class="todo-label todo-label-done" name="todo-done" value="{{id}}" type="submit">&#x2611; {{label}}</button>
            <button class="todo-remove" name="todo-remove" value="{{id}}" type="submit">remove</button>
            {{/done}}
        </div>
        {{/todos}}
    </form>
    <div>{{count}} TODOs</div>
</body>
</html>
'''


def handler(system: flow_api.System, this: flow_api.Execution):
    store = system.setting('todo-store')
    try:
        todos = store.get('value')
    except flow_api.ResourceNotFoundError:
        todos = []
    if not todos:
        todos = []

    inputs = this.get('input_value')
    method = inputs['method']
    json = inputs['json']
    path = inputs['path']
    query = inputs['query']

    if method == 'POST':
        todo_new = json.get('todo-new')
        if todo_new:
            todos.append({
                'id': str(uuid.uuid4()),
                'label': todo_new,
            })
        todo_done = json.get('todo-done')
        if todo_done:
            todos = [
                {
                    **todo,
                    'done': not todo.get('done', False)
                }
                if todo['id'] == todo_done else todo
                for todo
                in todos
            ]
        todo_remove = json.get('todo-remove')
        if todo_remove:
            todos = [
                todo
                for todo
                in todos
                if todo['id'] != todo_remove
            ]

    store.save(value=todos)

    data = {
        'count': len(todos),
        'todos': todos,
    }
    if query.get('debug'):
        data.update({
            'debug': True,
            'method': method,
            'json': json,
            'path': path,
            'query': query,
        })

    return this.webhook_html_response(
        pystache.render(MAIN, data)
    )
