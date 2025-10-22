# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsdl2-mixer-2.0-0 \
    libsdl2-2.0-0 \
    libsdl2-image-2.0-0 \
    libsdl2-ttf-2.0-0 \
    libfreetype6 \
    libportmidi0 \
    libasound2 \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY server.py ./
COPY README.md ./

# Create downloads directory
RUN mkdir -p downloads

# Install Python dependencies using uv
RUN uv sync --frozen

# Set the default command to run the MCP server
CMD ["uv", "run", "--with", "fastmcp", "--with", "yt-dlp", "fastmcp", "run", "server.py"]
