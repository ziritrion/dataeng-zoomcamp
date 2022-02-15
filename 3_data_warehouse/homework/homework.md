### Question 1: 
**What is count for fhv vehicles data for year 2019**  
Can load the data for cloud storage and run a count(*)
> Code:
```sql
SELECT count(*)
FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`
WHERE DATE(pickup_datetime) BETWEEN "2019-01-01" AND "2019-12-31";
```
>Answer (correct):
```
42084899
```
>Proposed solution code:
```sql
-- Create a table with only the 2019 data for simplicity
CREATE OR REPLACE EXTERNAL TABLE `animated-surfer-338618.trips_data_all.fhv_tripdata`
OPTIONS (
  format = 'CSV',
  uris = ['gs://dtc_data_lake_animated-surfer-338618/fhv/fhv_tripdata_2019-*.csv']
);

-- Count of fhv trips
SELECT count(*) FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`;
```

### Question 2: 
**How many distinct dispatching_base_num we have in fhv for 2019**  
Can run a distinct query on the table from question 1
> Code:
```sql
SELECT count(DISTINCT(dispatching_base_num))
FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`
WHERE DATE(pickup_datetime) BETWEEN "2019-01-01" AND "2019-12-31";
```
>Answer (correct):
```
792
```
>Proposed solution code:
```sql
SELECT COUNT(DISTINCT(dispatching_base_num)) FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`;
```

### Question 3: 
**Best strategy to optimise if query always filter by dropoff_datetime and order by dispatching_base_num**  
Review partitioning and clustering video.   
We need to think what will be the most optimal strategy to improve query 
performance and reduce cost.
>Answer (correct):
```
Partition by dropoff_datetime and cluster by dispatching_base_num
```

### Question 4: 
**What is the count, estimated and actual data processed for query which counts trip between 2019/01/01 and 2019/03/31 for dispatching_base_num B00987, B02060, B02279**  
Create a table with optimized clustering and partitioning, and run a 
count(*). Estimated data processed can be found in top right corner and
actual data processed can be found after the query is executed.
>Code:
```sql
CREATE OR REPLACE TABLE `animated-surfer-338618.trips_data_all.fhv_tripdata_clustered`
PARTITION BY DATE(pickup_datetime)
CLUSTER BY dispatching_base_num AS
SELECT * FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`;

SELECT count(*)
FROM `animated-surfer-338618.trips_data_all.fhv_tripdata_clustered`
WHERE DATE(pickup_datetime) BETWEEN "2019-01-01" AND "2019-03-31"
AND dispatching_base_num IN ('B00987','B02060','B02279');
```
>Answer (correct):
```
Estimated data: 400.1MB
Processed data: 145.4MB
Count: 26647

Note: Processed data is only 145 (155 in the form) if we use a clustered table. On a non-clustered table it would process the full 400MB.

Note 2: using the proposed solution code, the processed data is 149MB and the count is 26658.
```
>Proposed solution code:
```sql
-- This code assumes that fhv_tripdata only contains 2019 data
-- Non-partitioned table
CREATE OR REPLACE TABLE `animated-surfer-338618.trips_data_all.fhv_nonpartitioned_tripdata`
AS SELECT * FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`;

-- Partitioned and clustered table
CREATE OR REPLACE TABLE `animated-surfer-338618.trips_data_all.fhv_partitioned_tripdata`
PARTITION BY DATE(dropoff_datetime)
CLUSTER BY dispatching_base_num AS (
  SELECT * FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`
);

SELECT count(*) FROM  `animated-surfer-338618.trips_data_all.fhv_nonpartitioned_tripdata`
WHERE dropoff_datetime BETWEEN '2019-01-01' AND '2019-03-31'
  AND dispatching_base_num IN ('B00987', 'B02279', 'B02060');
```

### Question 5: 
**What will be the best partitioning or clustering strategy when filtering on dispatching_base_num and SR_Flag**  
Review partitioning and clustering video. 
Clustering cannot be created on all data types.
>Code:
```sql
SELECT count(DISTINCT(SR_Flag))
FROM `animated-surfer-338618.trips_data_all.fhv_tripdata`
WHERE DATE(pickup_datetime) BETWEEN "2019-01-01" AND "2019-03-31";
```
>Answer (dispute):
```
Partition by SR_Flag and cluster by dispatching_base_num

Partitions can only be done on timestamps, dates or integers and there's a limit of 4000 partitions. SR_Flag is an integer and using the code above we can see that there are 43 distinct SR_Flag values, so we can use it for partitioning. Clustering can be done on Strings and dispatching_base_num is a string, so we cluster by it.
```
>Proposed solution:
```
Cluster by SR_Flag and dispatching_base_num

In the proposed code, the SR_Flag field appears as a String rather than an Integer which means that we could not use it for partitioning. However, if SR_Flag is an integer as it is in my case, then my solution is correct.
```

### Question 6: 
**What improvements can be seen by partitioning and clustering for data size less than 1 GB**  
Partitioning and clustering also creates extra metadata.  
Before query execution this metadata needs to be processed.

>Answer (correct):
```
(Multiple choice)
No improvements
Can be worse due to metadata
```

### (Not required) Question 7: 
**In which format does BigQuery save data**  
Review big query internals video.

>Answer (correct):
```
Columnar
```
