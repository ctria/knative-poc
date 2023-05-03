import json
import os
import time
import uuid

from flask import Flask, make_response, request
from redis import StrictRedis

redis_host = os.environ.get('REDIS_HOST', 'localhost')

redis = StrictRedis(host=redis_host, port=6379)

app = Flask(__name__)

@app.route('/', methods=['POST'])
def root():
    task = json.loads(redis.hget('tasks', request.headers['Ce-Id']) or '{}')
    task['started'] = time.strftime('%d/%m/%y %H:%M:%S')
    redis.hset('tasks', request.headers['Ce-Id'], json.dumps(task))

    try:
        sleep_time = request.json.get('duration', 0)
    except:
        sleep_time = 0
    start = time.strftime('%d/%m/%y %H:%M:%S')
    time.sleep(sleep_time)
    end = time.strftime('%d/%m/%y %H:%M:%S')
    response = make_response({
        'start': start,
        'end': end,
        'sleep_time': sleep_time
    })
    response.headers["Ce-Id"] = request.headers.get("Ce-Id", str(uuid.uuid4()))
    response.headers["Ce-Source"] = request.host
    response.headers["Ce-specversion"] = "1.0"
    response.headers["Ce-Type"] = "task-result"
    return response

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
