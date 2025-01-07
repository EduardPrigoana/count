from flask import Flask, redirect, request
from collections import defaultdict

app = Flask(__name__)
app.url_map.strict_slashes = False

visit_counts = defaultdict(int)

@app.route('/')
def home():
    return redirect("https://prigoana.com/count")

@app.route('/<handle>')
def handle_request(handle):
    add_value = request.args.get('add', default=0, type=int)
    subtract_value = request.args.get('subtract', default=0, type=int)

    visit_counts[handle] += 1
    count = visit_counts[handle] + add_value - subtract_value

    return str(count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
