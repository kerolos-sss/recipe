# Use the official Python image from the Docker Hub
FROM python:3.9-alpine3.13
LABEL maintainer="kerolos.sss@gmail.com"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
RUN apk update \
    && apk add --no-cache gcc musl-dev postgresql-dev

# Add a user with disabled password and no home directory
# RUN adduser -D -H -s /bin/false appuser
RUN adduser --disabled-password --no-create-home django-user

# Install Python dependencies
COPY requirements.txt /app/
RUN python -m venv /py \
    && apk add --update --no-cache postgresql-client \
    && apk add --no-cache --virtual .build-deps \
        build-base musl-dev postgresql-dev \
    && /py/bin/pip install --upgrade pip \
    && /py/bin/pip install -r requirements.txt

RUN PATH="/py/bin:$PATH"

ARG DEV=false
COPY requirements-dev.txt /app/
RUN if [ "$DEV" = "true" ]; then \
    echo "Running in development mode"; \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r requirements-dev.txt ; \
    else \
    echo "Running in production mode"; \
    fi \ 
    && apk del .build-deps
ENV PATH="/py/bin:$PATH"

USER django-user
# Copy project
COPY app/ /app/
# Expose port 8000
EXPOSE 8000

# Run the Django development server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "recipe.wsgi:application"]
