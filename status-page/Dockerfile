FROM python:3.9-slim

WORKDIR /app

# Install required packages
RUN pip install flask requests

# Copy the application
COPY status_app.py .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "status_app.py"]