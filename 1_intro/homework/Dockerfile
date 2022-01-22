FROM python:3.9.1

RUN apt-get install wget
RUN pip install pandas sqlalchemy psycopg2

WORKDIR /app
COPY ingest_data.py ingest_data.py
COPY trips.csv trips.csv
COPY zones.csv zones.csv

ENTRYPOINT [ "python", "ingest_data.py" ]