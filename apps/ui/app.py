import json
import os
import sys
import time
import uuid

import requests
from flask import (Flask, flash, make_response, redirect, render_template,
                   request, url_for)
from redis import StrictRedis

app = Flask(__name__)
app.secret_key = os.urandom(24)

broker_url = os.environ.get('BROKER_URL')
redis_host = os.environ.get('REDIS_HOST', 'localhost')

redis = StrictRedis(host=redis_host, port=6379)

if not broker_url:
    print("The BROKER_URL environment variable is not set")
    sys.exit(1)

@app.route('/tasks', methods=['GET'])
def tasks():
    task_list = []
    redis_tasks = redis.hgetall('tasks')
    for task in redis_tasks:
        task_info = json.loads(redis_tasks[task].decode())
        task_list.append([
            task.decode(),
            task_info.get('scheduled', ''),
            task_info.get('started', ''),
            task_info.get('finished', ''),
            json.dumps(task_info.get('data', None)),
            json.dumps(task_info.get('result', None)),
        ])
    response = make_response({"data": task_list})
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def send_events():
    event_count = int(request.form.get("event_count", "1"))
    duration = int(request.form.get("duration", "10"))

    headers = {
        'Ce-specversion': '1.0',
        'Ce-Type': 'sleep',
        'Ce-Source': 'knative-ui'
    }

    for _ in range(0, event_count):
        data = {'duration': duration}
        task_id = str(uuid.uuid4())
        task_data = {'scheduled': time.strftime('%d/%m/%y %H:%M:%S'), 'data': data}
        redis.hset('tasks', task_id, json.dumps(task_data))
        headers['Ce-Id'] = task_id
        requests.post(broker_url, headers=headers, json=data, timeout=60)

    flash(f"{event_count} tasks queued for {duration}")
    return redirect(url_for('index'))

@app.route('/result', methods=['POST'])
def result():
    task = json.loads(redis.hget('tasks', request.headers['Ce-Id']) or '{}')
    task['finished'] = time.strftime('%d/%m/%y %H:%M:%S')
    task['result'] = request.json
    redis.hset('tasks', request.headers['Ce-Id'], json.dumps(task))
    return("OK", 200)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
