FROM python:3.12-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy the MCP server code
COPY . /app/

# Install dependencies
RUN uv sync --no-cache

# Expose port for HTTP transport
EXPOSE 8000

# Set default environment variables
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

# Run the MCP server with HTTP transport
# Jenkins credentials should be provided via environment variables
CMD ["uv", "run", "python", "main.py", "--transport", "http"]
