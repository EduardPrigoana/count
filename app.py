import logging
import os
from typing import Set, Tuple

import redis
from flask import Flask, Response, abort, jsonify, request
from flask_cors import CORS
from redis.exceptions import ConnectionError as RedisConnectionError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

FORBIDDEN_EXACT: Set[str] = {
    "_phpinfo.php", "aws-secret.yml", "aws.yml", "backup.tar.gz",
    "backup.zip", "config.json", "config.yaml", "config.yml",
    ".env", ".env.local", ".env.production",
    "credentials.json", "database.sql", "db.sql", "debug.log",
    "dump.sql", "error.log", "info", "info.php", "phpinfo",
    "phpinfo.php", "secrets.json", "secrets.yml", "test_phpinfo.php",
    "wordpress"
}

FORBIDDEN_PREFIXES: Tuple[str, ...] = (
    ".",
    "docker-",
)

MAX_KEY_LENGTH = 1024

app = Flask(__name__)
CORS(app)

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    raise ValueError("REDIS_URL environment variable not set.")

try:
    r = redis.Redis.from_url(redis_url, decode_responses=True)
    r.ping()
    logging.info("Successfully connected to Redis.")
except RedisConnectionError as e:
    logging.error(f"Could not connect to Redis: {e}")
    r = None

@app.before_request
def block_forbidden_paths() -> None:
    path = request.path.strip("/")

    if path in FORBIDDEN_EXACT:
        logging.warning(f"Forbidden path access attempt (exact match): {path}")
        abort(403)

    if path.startswith(FORBIDDEN_PREFIXES):
        logging.warning(f"Forbidden path access attempt (prefix match): {path}")
        abort(403)


@app.route('/favicon.ico')
def favicon() -> Response:
    return Response(status=204)


@app.route('/', methods=['GET'])
def hello() -> str:
    return '1'


@app.route('/<string:h>/', methods=['GET'])
def get_count(h: str) -> Response:
    if len(h) > MAX_KEY_LENGTH:
        logging.warning(f"Key length exceeded: {len(h)} > {MAX_KEY_LENGTH}")
        abort(400, description="Key is too long.")

    if r is None:
        logging.error("Redis connection is not available.")
        abort(503, description="Service is temporarily unavailable.")

    try:
        count = r.incr(h)
        return jsonify({"count": count})

    except RedisConnectionError:
        logging.error("Could not connect to Redis during a request.")
        abort(503, description="Could not connect to the data store.")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)