# Base Image: Official Apache Airflow
FROM apache/airflow:2.9.0

# Switch to root to install system dependencies
USER root

# Install build-essential and git (often needed for compiling python libs)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         build-essential \
         git \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Switch back to the airflow user for Python package installation
USER airflow

# Copy the requirements.txt file into the container
COPY requirements.txt /requirements.txt

# Install the Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt