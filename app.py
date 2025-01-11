from flask import Flask, request, jsonify, send_file
from PIL import Image
import os
import zipfile
import io

app = Flask(__name__)

# In-memory store for counts
data_store = {}

# Helper function to create image for a count
def create_count_image(count, style, gap):
    count_str = str(count)
    images = []
    
    # Extract images from the zip file
    with zipfile.ZipFile(style, 'r') as z:
        for char in count_str:
            if char == '-':
                digit_file = "minus.ext"
            else:
                digit_file = f"{char}.ext"
            if digit_file in z.namelist():
                with z.open(digit_file) as file:
                    images.append(Image.open(file).convert("RGBA"))
            else:
                raise ValueError(f"Missing image for character: {char}")

    # Combine images with specified gap
    total_width = sum(img.width for img in images) + (len(images) - 1) * gap
    max_height = max(img.height for img in images)
    combined_image = Image.new("RGBA", (total_width, max_height), (255, 255, 255, 0))

    x_offset = 0
    for img in images:
        combined_image.paste(img, (x_offset, 0), img)
        x_offset += img.width + gap

    output = io.BytesIO()
    combined_image.save(output, format="PNG")
    output.seek(0)
    return output

@app.route('/<path:type>/<handle>/', methods=['GET'])
def get_count(type, handle):
    count = data_store.get(handle, 0)
    if type == "text":
        return jsonify({"count": count})
    elif type == "image":
        style = request.args.get("style")
        gap = int(request.args.get("gap", 0))

        if not style or not os.path.exists(style):
            return jsonify({"error": "Style zip file not provided or does not exist"}), 400

        try:
            image = create_count_image(count, style, gap)
            return send_file(image, mimetype="image/png")
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid path"}), 404

@app.route('/<path:type>/<handle>/value=<int:value>', methods=['POST'])
def set_initial_value(type, handle, value):
    data_store[handle] = value
    return jsonify({"message": f"Count for {handle} set to {value}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
