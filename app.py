from flask import Flask, redirect, request, jsonify, send_file
import requests
import zipfile
import io
from collections import defaultdict
from PIL import Image
import logging

app = Flask(__name__)
app.url_map.strict_slashes = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Visit counts
visit_counts = defaultdict(int)

# Style cache (keyed by style_url)
style_cache = {}

# Default home redirect
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

    try:
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

        if not is_valid_gap(gap):
            return jsonify({"error": "Invalid gap value. It must be a non-negative integer."}), 400

        # Return count as text if no style URL is provided
        if style_url is None:
            return str(count)

        # Cache the style URL and download the zip file if not already cached
        if style_url not in style_cache:
            try:
                style_cache[style_url] = download_and_cache_style(style_url)
            except Exception as e:
                logger.error(f"Error downloading or processing the style zip: {str(e)}")
                return jsonify({"error": f"Failed to fetch the style ZIP: {str(e)}"}), 400

        digits = str(count)
        images = [io.BytesIO(style_cache[style_url].get(digit, None)) for digit in digits]

        # Handle missing image data
        images = [image for image in images if image is not None]
        if not images:
            return jsonify({"error": "One or more images are missing in the zip file."}), 404

        combined_image = combine_images(images, gap)
        return send_file(combined_image, mimetype='image/png')

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Validate gap (must be non-negative)
def is_valid_gap(gap):
    return gap >= 0

# Download and cache the style zip file
def download_and_cache_style(style_url):
    try:
        response = requests.get(style_url)
        if response.status_code == 200:
            zip_data = zipfile.ZipFile(io.BytesIO(response.content))
            return {f"{i}": zip_data.read(f"{i}.png") for i in range(10)}
        else:
            raise Exception(f"Failed to download the ZIP, status code: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error processing ZIP file: {str(e)}")

# Combine images with gap
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

# If this is the main program, start the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
