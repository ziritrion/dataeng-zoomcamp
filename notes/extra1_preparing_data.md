 >[Back to Batch processing](5_batch_processing.md)

 >[Back to Index](README.md)
 
 # Extra: preparing yellow and green taxi data

 _[Video source](https://www.youtube.com/watch?v=CI3P4tAtru4&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=52)_

In order to minimize the errors and discrepancies of the previous lessons' homework, we will create a script that downloads the [datasets](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page) for 2020 and 2021 and parquetizes them with a predefined schema.

## Download the datasets

Let's create a `download_data.sh` script.

```bash
#!/bin/bash
set -e

TAXI_TYPE=$1 # "yellow"
YEAR=$2 # 2020

URL_PREFIX="https://s3.amazonaws.com/nyc-tlc/trip+data"

for MONTH in {1..12}; do
  FMONTH=`printf "%02d" ${MONTH}`

  URL="${URL_PREFIX}/${TAXI_TYPE}_tripdata_${YEAR}-${FMONTH}.csv"

  LOCAL_PREFIX="data/raw/${TAXI_TYPE}/${YEAR}/${FMONTH}"
  LOCAL_FILE="${TAXI_TYPE}_tripdata_${YEAR}_${FMONTH}.csv"
  LOCAL_PATH="${LOCAL_PREFIX}/${LOCAL_FILE}"

  echo "donwloading ${URL} to ${LOCAL_PATH}"
  mkdir -p ${LOCAL_PREFIX}
  wget ${URL} -O ${LOCAL_PATH}

  echo "compressing ${LOCAL_PATH}"
  gzip ${LOCAL_PATH}
done
```
* The script loops through 12 months and downloads the dataset for each month for the specified taxi type; we compress the csv files to zip for saving storage (both Pandas and Spark can read zipped datasets).
* `set -e` means that the script will stop if any of the commands fail. This may happen with `wget` when we download files.
* We parametrize each part of the dataset URL. For the month, we need to convert the month numnber to 2-digits with leading zeros for single-digit months.
* `printf` is a shell built-in command available in bash and other shells which behaves very similar to C's `printf()` function. It can be used instead of `echo` for finer output control.
    * The syntax for the command is `printf [-v var] format [arguments]`
        * The `[-v var]` option is for assigning the output to a variable rather than printing it.
        * `format` is a string that may contain normal characters, backslash-escaped characters and conversion specifications for describing the format.
            * Conversion specifications follow this syntax: `%[flags][width][.precision]specifier`
        * `[arguments]` is a list of arguments of any length that will be passed to the `format` string.
    * `printf "%02d" ${MONTH}` means that the `${MONTH}` argument will be reformatted to show 2 digits with a leading 0 for single digit months.
        * `%` is the conversion specification character.
        * `0` is a flag for padding with leading zeroes.
        * `2` is a width directive; in our case, it means that the output should be of length 2.
        * `d` is the type conversion specifier for signed decimal integers.
    * You may learn more about the `printf` command [in this link](https://linuxize.com/post/bash-printf-command/).
* `mkdir -p` creates both the final directory and its parent directories if they do not exist.
* The `-O` option in `wget ${URL} -O ${LOCAL_PATH}` is for specifying the file name.
* `gzip ${LOCAL_PATH}` will compress the downloaded files to `gz` format.
    * By default, `gzip` deletes the original file after compressing it. CSV files will be removed.
    * `gz` files can be read by both Pandas and Spark.

Make the script executable with `chmod +x download_data.sh`. You may run the script with `./download_data.sh yellow 2020`. You may change yellow to `green` and `2020` to any year. For the rest of the lesson we will use the datasets for 2020 and 2021.

After running the script, you may check the final folder structure with `tree`, `df -h` or `du -h`.

You may download a finished script [from this link](../5_batch_processing/download_data.sh).

_[Back to the top](#)_

## Parquetize the datasets

We will use the same [Pandas trick we saw in part 5 of lesson 4](5_batch_processing.md#reading-csv-files) to read the datasets, infer the schemas, partition the datasets and parquetize them.

The schema for yellow and green taxis will be the following:

```python
from pyspark.sql import types

green_schema = types.StructType([
    types.StructField("VendorID", types.IntegerType(), True),
    types.StructField("lpep_pickup_datetime", types.TimestampType(), True),
    types.StructField("lpep_dropoff_datetime", types.TimestampType(), True),
    types.StructField("store_and_fwd_flag", types.StringType(), True),
    types.StructField("RatecodeID", types.IntegerType(), True),
    types.StructField("PULocationID", types.IntegerType(), True),
    types.StructField("DOLocationID", types.IntegerType(), True),
    types.StructField("passenger_count", types.IntegerType(), True),
    types.StructField("trip_distance", types.DoubleType(), True),
    types.StructField("fare_amount", types.DoubleType(), True),
    types.StructField("extra", types.DoubleType(), True),
    types.StructField("mta_tax", types.DoubleType(), True),
    types.StructField("tip_amount", types.DoubleType(), True),
    types.StructField("tolls_amount", types.DoubleType(), True),
    types.StructField("ehail_fee", types.DoubleType(), True),
    types.StructField("improvement_surcharge", types.DoubleType(), True),
    types.StructField("total_amount", types.DoubleType(), True),
    types.StructField("payment_type", types.IntegerType(), True),
    types.StructField("trip_type", types.IntegerType(), True),
    types.StructField("congestion_surcharge", types.DoubleType(), True)
])

yellow_schema = types.StructType([
    types.StructField("VendorID", types.IntegerType(), True),
    types.StructField("tpep_pickup_datetime", types.TimestampType(), True),
    types.StructField("tpep_dropoff_datetime", types.TimestampType(), True),
    types.StructField("passenger_count", types.IntegerType(), True),
    types.StructField("trip_distance", types.DoubleType(), True),
    types.StructField("RatecodeID", types.IntegerType(), True),
    types.StructField("store_and_fwd_flag", types.StringType(), True),
    types.StructField("PULocationID", types.IntegerType(), True),
    types.StructField("DOLocationID", types.IntegerType(), True),
    types.StructField("payment_type", types.IntegerType(), True),
    types.StructField("fare_amount", types.DoubleType(), True),
    types.StructField("extra", types.DoubleType(), True),
    types.StructField("mta_tax", types.DoubleType(), True),
    types.StructField("tip_amount", types.DoubleType(), True),
    types.StructField("tolls_amount", types.DoubleType(), True),
    types.StructField("improvement_surcharge", types.DoubleType(), True),
    types.StructField("total_amount", types.DoubleType(), True),
    types.StructField("congestion_surcharge", types.DoubleType(), True)
])
```

You may download a finished Jupyter Notebook script [from this file](../5_batch_processing/05_taxi_schema.ipynb).

_[Back to the top](#)_

 >[Back to Batch processing](5_batch_processing.md)

 >[Back to Index](README.md)