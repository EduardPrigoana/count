from flask import Flask, request, jsonify
from urllib.parse import unquote

app = Flask(__name__)

# Dictionary to track counters
counters = {}

@app.route('/')
def root():
    return "Visit: https://prigoana.com/count", 200

# Helper function to extract value and style URL
def parse_value_and_style(args):
    value = args.get('value', type=int, default=0)
    style_url = args.get('style', type=str, default=None)
    if style_url:
        style_url = unquote(style_url)  # Decode the encoded URL
    return value, style_url

@app.route('/<handle>/', defaults={'trailing': ''})
@app.route('/<handle>', defaults={'trailing': ''})
@app.route('/<handle>/value=<int:value>/', defaults={'trailing': ''})
@app.route('/<handle>/value=<int:value>', defaults={'trailing': ''})
@app.route('/<handle>/style/<path:style_url>/', defaults={'trailing': ''})
@app.route('/<handle>/style/<path:style_url>', defaults={'trailing': ''})
@app.route('/<handle>/value=<int:value>/style/<path:style_url>/', defaults={'trailing': ''})
@app.route('/<handle>/style/<path:style_url>/value=<int:value>/', defaults={'trailing': ''})
def handle_requests(handle, value=0, style_url=None, trailing=''):
    # Update counter for the handle
    if handle not in counters:
        counters[handle] = 0

    # Parse query parameters for flexibility
    query_value, query_style_url = parse_value_and_style(request.args)
    value += query_value
    style_url = style_url or query_style_url

    # Update counter
    counters[handle] += value

    # If style URL is provided, simulate its usage
    if style_url:
        if not style_url.endswith('.zip'):
            return "Error: Only .zip files are supported for styles.", 400
        return jsonify({
            "handle": handle,
            "count": counters[handle],
            "style_url": style_url
        })

    # Default response: Just return the count
    return jsonify({
        "handle": handle,
        "count": counters[handle]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
