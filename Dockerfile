# Base Image: Official Airflow
FROM apache/airflow:2.9.0

USER root

# 1. Install System Dependencies (Java, Git, Build Tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  git \
  curl \
  openjdk-17-jre-headless \
  procps \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# 2. Set Java Home (Critical for Spark)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# 3. Download Azure Cloud Connectors for Spark (Hadoop 3.3.4 compatible)
# These allow Spark to speak "abfss://" protocol
WORKDIR /opt/spark-jars
RUN curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-azure/3.3.4/hadoop-azure-3.3.4.jar && \
  curl -O https://repo1.maven.org/maven2/com/microsoft/azure/azure-storage/8.6.6/azure-storage-8.6.6.jar

USER airflow

# 4. Install Python Dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt