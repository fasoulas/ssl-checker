# Use a slim base image with Python
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy code into container
COPY ssl_checker.py .

# Install dependencies
RUN pip install fastapi uvicorn "pydantic>=2.0.0"

# Default command: run FastAPI app
CMD ["uvicorn", "ssl_checker:app", "--host", "0.0.0.0", "--port", "8000"]