# Start from an official Python runtime image
FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim

# Set the working directory in the container
WORKDIR /code

# Copy only the requirements file first for improved Docker caching
COPY ./requirements /code/requirements

# Install Python dependencies using uv
# Note: --system is required because uv refuses to install into the system Python by default
RUN uv pip install --system --no-cache -r /code/requirements

# Copy the application code and migration files
COPY ./app /code/app
COPY ./alembic /code/alembic
COPY ./alembic.ini /code/alembic.ini
COPY ./pyproject.toml /code/pyproject.toml

# Ensure Python can find the 'app' module
ENV PYTHONPATH=/code

# Command to run the application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]