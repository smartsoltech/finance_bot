# Use an official Python runtime based on Alpine as a parent image
FROM python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Add build dependencies, then install Python packages, and remove build dependencies
# This is a common pattern when using Alpine to keep the image size small
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps && apt install -y sqlite

# Make port 80 available to the world outside this container
EXPOSE 8090

# Define environment variable
ENV NAME World

# Run bot.py when the container launches
CMD ["python3", "bot.py"]

