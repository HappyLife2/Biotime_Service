# Use official lightweight Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (default for uvicorn/fastapi)
EXPOSE 8000

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Command to run the application using Uvicorn
# In production, you might want to consider Gunicorn with Uvicorn workers,
# but Uvicorn alone is often sufficient for modern async apps.
CMD ["uvicorn", "biotime_service:app", "--host", "0.0.0.0", "--port", "8000"]
