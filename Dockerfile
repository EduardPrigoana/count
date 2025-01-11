# Use Python slim image
FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Copy app files to container
COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
