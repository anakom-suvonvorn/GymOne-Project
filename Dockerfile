# Use the official Python 3.11 slim image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv globally in the container
RUN pip install uv

# Copy ONLY the pyproject.toml first (and uv.lock if you have one)
# We do this first so Docker caches the installed dependencies unless you change this file
COPY pyproject.toml ./
# COPY uv.lock ./ 

# Use uv to install dependencies into the system python environment
RUN uv pip install --system -r pyproject.toml

# Copy your routers directory
COPY routers/ ./routers/

# Copy all your root Python scripts
COPY *.py ./

# Expose the port your FastAPI app will run on
EXPOSE 8000

CMD ["python", "main.py"]