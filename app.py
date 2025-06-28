import os
from flask import Flask, jsonify, Response
import redis
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/<h>/', methods=['GET'])
def get_count(h):
    count = r.incr(h)
    return jsonify({"count": count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
