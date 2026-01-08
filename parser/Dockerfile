FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy parser package
COPY parser /app/parser

# Create state directory
RUN mkdir -p /state

# Set environment variable for state path
ENV STATE_PATH=/state/parser_state.json

# Run parser
CMD ["python", "-m", "parser.cli"]
