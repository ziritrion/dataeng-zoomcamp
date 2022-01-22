#!/usr/bin/env python
# coding: utf-8

import os
import argparse

from time import time

import pandas as pd
from sqlalchemy import create_engine


def main(params):
    user = params.user
    password = params.password
    host = params.host 
    port = params.port 
    db = params.db
    table_name_1 = params.table_name_1
    table_name_2 = params.table_name_2
    url1 = 'https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2021-01.csv'
    url2 = 'https://s3.amazonaws.com/nyc-tlc/misc/taxi+_zone_lookup.csv'
    csv1 = 'trips.csv'
    csv2 = 'zones.csv'

    # download the CSV files
    print('checking files')
    csv1_exists = os.path.exists(csv1)
    csv2_exists = os.path.exists(csv2)
    if csv1_exists:
        print('csv1 - trips already exists')
    else:
        print('downloading csv1 - trips')
        os.system(f"wget {url1} -O {csv1}")
        csv1_exists = os.path.exists(csv1)
    if csv2_exists:
        print('csv2 - zones already exists')
    else:
        print('downloading csv2 - zones')
        os.system(f"wget {url2} -O {csv2}")
    print('finished downloading files')

    # create db connection
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    # trips
    print('inserting trips to database')
    df_iter = pd.read_csv(csv1, iterator=True, chunksize=100000)
    df = next(df_iter)
    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    df.head(n=0).to_sql(name=table_name_1, con=engine, if_exists='replace')
    df.to_sql(name=table_name_1, con=engine, if_exists='append')
    for chunk in df_iter:
        t_start = time()
        df = chunk
        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
        df.to_sql(name=table_name_1, con=engine, if_exists='append')
        t_end = time()
        print('inserted another chunk, took %.3f second' % (t_end - t_start))
    print('finished inserting trips to database')
    
    # zones
    print('inserting zones to database')
    df =pd.read_csv(csv2)
    df.to_sql(name=table_name_2, con=engine, if_exists='append')
    print('finished inserting zones to database')


if __name__ == '__main__':
    # Parse the command line arguments and calls the main program
    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')

    parser.add_argument('--user', help='user name for postgres')
    parser.add_argument('--password', help='password for postgres')
    parser.add_argument('--host', help='host for postgres')
    parser.add_argument('--port', help='port for postgres')
    parser.add_argument('--db', help='database name for postgres')
    parser.add_argument('--table_name_1', help='name of the table for trips')
    parser.add_argument('--table_name_2', help='name of the table for zones')
    #parser.add_argument('--url', help='url of the csv file')

    args = parser.parse_args()

    main(args)