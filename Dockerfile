FROM apache/airflow:2.9.2-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    dbt-bigquery==1.8.2 \
    google-cloud-bigquery==3.25.0 \
    google-cloud-storage==2.17.0 \
    requests \
    python-dotenv \
    pandas \
    isodate \
    tqdm
