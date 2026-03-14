# Start from an official Python runtime image
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Set the working directory in the container
WORKDIR /code

# Copy only the requirements file first for improved Docker caching
COPY ./requirements /code/requirements

# Install Python dependencies using uv
# Note: --system is required because uv refuses to install into the system Python by default
RUN uv pip install --system --no-cache -r /code/requirements

# Copy the rest of the application code
COPY ./app /code/app

# Command to run the application using gunicorn (production WSGI server)
# Use the exec form of CMD for proper signal handling
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "app.main:app"]