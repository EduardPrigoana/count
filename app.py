import os
from flask import Flask, jsonify, Response, request, abort
import redis
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

r = redis.Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

# List of exact forbidden paths
FORBIDDEN_EXACT = {
    "_phpinfo.php",
    "aws-secret.yml",
    "aws.yml",
    "backup.tar.gz",
    "backup.zip",
    "config.json",
    "config.yaml",
    "config.yml",
    "credentials.json",
    "database.sql",
    "db.sql",
    "debug.log",
    "dump.sql",
    "error.log",
    "info",
    "info.php",
    "phpinfo",
    "phpinfo.php",
    "secrets.json",
    "secrets.yml",
    "test_phpinfo.php",
    "wordpress"
}

# Prefixes that are forbidden
FORBIDDEN_PREFIXES = (
    ".",
    "docker-"
)

@app.before_request
def block_forbidden_paths():
    # Get the path without leading slash
    path = request.path.strip("/")

    # If it matches an exact forbidden path
    if path in FORBIDDEN_EXACT:
        abort(403)

    # If it starts with any forbidden prefix
    for prefix in FORBIDDEN_PREFIXES:
        if path.startswith(prefix):
            abort(403)

@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/', methods=['GET'])
def hello():
    return '1'

@app.route('/<h>/', methods=['GET'])
def get_count(h):
    count = r.incr(h)
    return jsonify({"count": count})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
