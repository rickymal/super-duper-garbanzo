# Use the official Python 3.12 image from Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code to the container
COPY . .

# Expose any necessary ports (if your application uses them)
# EXPOSE 8000

# Define environment variables (if needed)
# ENV PYTHONUNBUFFERED=1

# Command to run your application
CMD ["python", "your_main_script.py"]
