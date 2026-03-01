FROM nikolaik/python-nodejs:python3.11-nodejs20-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install Git and clean up layer cache
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install the exact matching Gemini CLI globally
RUN npm install -g @google/gemini-cli@0.29.7

# Set up Python backend
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Render exposes the deployment port via the standard PORT env var
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]
