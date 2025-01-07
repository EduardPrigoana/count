import logging
from flask import Flask, request, jsonify
from PIL import Image
import os

# Initialize the Flask app
app = Flask(__name__)

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Route to handle image processing or other logic
@app.route('/process', methods=['GET', 'POST'])
def handle_request():
    try:
        # Get parameters from the URL query string
        handle = request.args.get('handle', type=str)
        style_url = request.args.get('style_url', type=str)
        value = request.args.get('value', type=int)  # Expects an integer value
        gap = request.args.get('gap', type=int)      # Expects an integer value
        
        # Validate parameters
        if value is None:
            return jsonify({"error": "Missing or invalid 'value' parameter"}), 400
        if gap is None:
            return jsonify({"error": "Missing or invalid 'gap' parameter"}), 400
        if not handle or not style_url:
            return jsonify({"error": "Missing 'handle' or 'style_url' parameter"}), 400
        
        # Your business logic or image processing can go here
        return jsonify({
            "message": "Request processed successfully",
            "handle": handle,
            "style_url": style_url,
            "value": value,
            "gap": gap
        }), 200
    
    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route to handle image file uploads
@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Get the image file from the request
        image_file = request.files.get('image')
        if image_file is None:
            return jsonify({"error": "No image file provided"}), 400
        
        # Try opening the image
        try:
            image = Image.open(image_file)
        except IOError as e:
            logging.error(f"Image processing error: {str(e)}")
            return jsonify({"error": "Invalid image data"}), 400
        
        # Process the image as required (example: save or apply filters)
        # For now, we are just sending a success message
        return jsonify({"message": "Image processed successfully"}), 200
    
    except Exception as e:
        logging.error(f"Unexpected error while processing image: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route to handle zip file or text-based input
@app.route('/process-zip-or-text', methods=['POST'])
def process_zip_or_text():
    try:
        zip_file = request.files.get('zip_file')
        if zip_file:
            # Implement your zip file handling logic here
            return jsonify({"message": "Zip file processed successfully"}), 200
        else:
            text_input = request.form.get('text_input')
            if not text_input:
                return jsonify({"error": "No text input provided"}), 400
            
            return jsonify({"message": "Text input processed successfully", "text_input": text_input}), 200
    
    except Exception as e:
        logging.error(f"Error processing zip or text input: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# General error handler
@app.errorhandler(404)
def not_found_error(error):
    logging.error(f"404 Error: {str(error)}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"500 Error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# Root URL redirect to 'count.prigoana.com'
@app.route('/')
def redirect_root():
    return jsonify({"message": "Redirecting to count.prigoana.com"}), 302, {'Location': 'https://count.prigoana.com'}

# Main entry point to run the app
if __name__ == '__main__':
    # Use the port provided by Render
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if not set by environment
    app.run(host='0.0.0.0', port=port, debug=True)
