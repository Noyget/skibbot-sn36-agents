FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy agents and requirements
COPY agents/ /app/agents/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for /act endpoint
EXPOSE 8000

# Run the agent server
CMD ["python", "-m", "agents.server"]
