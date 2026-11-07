FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory
RUN mkdir -p data

# Expose port
EXPOSE ${PORT:-8080}

# Run the app
CMD ["python", "main.py"]
