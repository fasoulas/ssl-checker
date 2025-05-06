# Use a slim base image with Python
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy code into container
COPY requirements.txt ./requirements.txt
COPY domain  ./domain
COPY check_ssl_mcp ./check_ssl_mcp
COPY ssl_checker.egg-info ./ssl_checker.egg-info
COPY setup.py ./setup.py

# Install dependencies
RUN cd /app/
RUN pip install -r requirements.txt 
RUN pip install -e . 

EXPOSE 8000

CMD ["uvicorn", "check_ssl_mcp.main:app", "--host", "0.0.0.0", "--port", "8000"]