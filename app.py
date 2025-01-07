from flask import Flask, redirect, request, jsonify, send_file
import requests
import zipfile
import io
from collections import defaultdict
from PIL import Image

app = Flask(__name__)
app.url_map.strict_slashes = False

visit_counts = defaultdict(int)
style_cache = {}

@app.route('/')
def home():
    return redirect("https://prigoana.com/count")

# Handle all combinations of style, value, and gap using hashtags
@app.route('/<handle>#style=<path:style_url>#gap=<int:gap>#value=<int:value>', defaults={'style_url': None, 'value': None, 'gap': 0})
@app.route('/<handle>#style=<path:style_url>#gap=<int:gap>', defaults={'value': None})
@app.route('/<handle>#style=<path:style_url>#value=<int:value>', defaults={'gap': 0})
@app.route('/<handle>#gap=<int:gap>#value=<int:value>', defaults={'style_url': None})
@app.route('/<handle>#style=<path:style_url>', defaults={'value': None, 'gap': 0})
@app.route('/<handle>#gap=<int:gap>', defaults={'style_url': None, 'value': None})
@app.route('/<handle>#value=<int:value>', defaults={'style_url': None, 'gap': 0})
def handle_request(handle, style_url, value, gap):
    global visit_counts

    # Increase visit count
    visit_counts[handle] += 1
    count = visit_counts[handle]

    # Adjust the count based on the value if present
    if value is not None:
        count += value

    # Use query parameters if provided
    if 'style' in request.args:
        style_url = request.args['style']

    if 'gap' in request.args:
        gap = int(request.args['gap'])

    if 'value' in request.args:
        value = int(request.args['value'])
        count += value

    if style_url is None:
        return str(count)

    # Cache the style URL and download the zip file if not already cached
    if style_url not in style_cache:
        try:
            response = requests.get(style_url)
            if response.status_code == 200:
                zip_data = zipfile.ZipFile(io.BytesIO(response.content))
                style_cache[style_url] = {f"{i}": zip_data.read(f"{i}.png") for i in range(10)}
            else:
                return jsonify({"error": "Failed to fetch the style ZIP"}), 400
        except Exception as e:
            return jsonify({"error": f"Failed to process the style ZIP: {str(e)}"}), 400

    try:
        digits = str(count)
        images = [io.BytesIO(style_cache[style_url][digit]) for digit in digits]
        combined_image = combine_images(images, gap)
        return send_file(combined_image, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": f"Failed to generate styled output: {str(e)}"}), 500

def combine_images(images, gap):
    pil_images = [Image.open(image) for image in images]
    total_width = sum(image.width for image in pil_images) + gap * (len(pil_images) - 1)
    max_height = max(image.height for image in pil_images)
    combined = Image.new('RGBA', (total_width, max_height))

    x_offset = 0
    for img in pil_images:
        combined.paste(img, (x_offset, 0))
        x_offset += img.width + gap

    output = io.BytesIO()
    combined.save(output, format='PNG')
    output.seek(0)
    return output

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)