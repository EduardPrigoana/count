FROM python:3.9-slim

WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt .

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
