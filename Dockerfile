# Dockerfile for Apache Airflow with custom dependencies

# Base Image: Official Apache Airflow
FROM apache/airflow:2.9.0

# Switch to root to install system dependencies
USER root

# Install system dependencies (ADD curl)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         git \
         curl \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt
