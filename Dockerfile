
FROM python:3.10-slim

WORKDIR /app

COPY src/ .


# Make port 5000 available
EXPOSE 5000

# Define environment variable with default value
ENV NODE_ID=node3


CMD ["python", "app.py"]