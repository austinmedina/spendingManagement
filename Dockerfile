FROM python:3.14-slim

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    git \
    vim \
    nano \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --no-cache-dir \
    flask \
    gunicorn \
    werkzeug \
    black \
    flake8 \
    pylint \
    pytest \
    ipython \
    debugpy

# Create non-root user with sudo access for development
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/appuser && \
    chmod 0440 /etc/sudoers.d/appuser

# Create necessary directories
RUN mkdir -p /workspace/receipts /workspace/uploads /workspace/static && \
    chown -R appuser:appuser /workspace

# Switch to non-root user
USER appuser

# Set up Python path
ENV PYTHONPATH=/workspace
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Expose port
EXPOSE 5000

# Keep container running for devcontainer
CMD ["tail", "-f", "/dev/null"]