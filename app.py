from flask import Flask, jsonify
from flask_cors import CORS
import os
import redis

app = Flask(__name__)
CORS(app)
r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

@app.route('/<h>/', methods=['GET'])
def get_count(h):
    count = r.incr(h)
    return jsonify({"count": count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
