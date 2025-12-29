# Dockerfile for Apache Airflow with custom dependencies

# Base Image: Official Apache Airflow
FROM apache/airflow:2.9.0

# Switch to root to install system dependencies
USER root

# Install system dependencies
# Added: openjdk-17-jre-headless (Required for PySpark)
# Added: procps (Required for PySpark to check status)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         git \
         curl \
         openjdk-17-jre-headless \
         procps \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Switch back to airflow user
USER airflow

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt