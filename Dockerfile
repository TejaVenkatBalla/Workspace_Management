# Use official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt



# Expose port 8000 for the Django app
EXPOSE 8000

# Set environment variable for Django settings module
ENV DJANGO_SETTINGS_MODULE=home.settings

# Run migrations, custom commands, and then the Django development server
CMD ["sh", "-c", "python manage.py migrate && python manage.py create_timeslots && python manage.py create_rooms && python manage.py runserver 0.0.0.0:8000"]
