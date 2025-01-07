from flask import Flask, redirect, request
from collections import defaultdict

app = Flask(__name__)
app.url_map.strict_slashes = False

visit_counts = defaultdict(int)

@app.route('/')
def home():
    return redirect("https://prigoana.com/count")

@app.route('/<handle>', defaults={'value': 0})
@app.route('/<handle>/value=<int:value>', defaults={})
def handle_request(handle, value):
    visit_counts[handle] += 1
    count = visit_counts[handle] + value
    return str(count)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)