FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir flask pillow requests

# Expose port 5000 (the default Flask port)
EXPOSE 5000

# Start the app with the correct entry point
CMD ["python", "app.py"]
