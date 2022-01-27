## Week 1 Homework

In this homework we'll prepare the environment 
and practice with terraform and SQL

## Question 1. Google Cloud SDK

Install Google Cloud SDK. What's the version you have? 

To get the version, run `gcloud --version`

>Answer:
```
368.0.0
```
>Full output for gcloud --version:
```
Google Cloud SDK 368.0.0
alpha 2022.01.07
beta 2022.01.07
bq 2.0.72
core 2022.01.07
gsutil 5.6
```

## Google Cloud account 

Create an account in Google Cloud and create a project.


## Question 2. Terraform 

Now install terraform and go to the terraform directory (`week_1_basics_n_setup/1_terraform_gcp/terraform`)

After that, run

* `terraform init`
* `terraform plan`
* `terraform apply` 

Apply the plan and copy the output (after running `apply`) to the form

>Answer:
```
var.project
  Your GCP Project ID

  Enter a value: <omitted>


Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # google_bigquery_dataset.dataset will be created
  + resource "google_bigquery_dataset" "dataset" {
      + creation_time              = (known after apply)
      + dataset_id                 = "trips_data_all"
      + delete_contents_on_destroy = false
      + etag                       = (known after apply)
      + id                         = (known after apply)
      + last_modified_time         = (known after apply)
      + location                   = "europe-west6"
      + project                    = "<omitted>"
      + self_link                  = (known after apply)

      + access {
          + domain         = (known after apply)
          + group_by_email = (known after apply)
          + role           = (known after apply)
          + special_group  = (known after apply)
          + user_by_email  = (known after apply)

          + view {
              + dataset_id = (known after apply)
              + project_id = (known after apply)
              + table_id   = (known after apply)
            }
        }
    }

  # google_storage_bucket.data-lake-bucket will be created
  + resource "google_storage_bucket" "data-lake-bucket" {
      + force_destroy               = true
      + id                          = (known after apply)
      + location                    = "EUROPE-WEST6"
      + name                        = "dtc_data_lake_<omitted>"
      + project                     = (known after apply)
      + self_link                   = (known after apply)
      + storage_class               = "STANDARD"
      + uniform_bucket_level_access = true
      + url                         = (known after apply)

      + lifecycle_rule {
          + action {
              + type = "Delete"
            }

          + condition {
              + age                   = 30
              + matches_storage_class = []
              + with_state            = (known after apply)
            }
        }

      + versioning {
          + enabled = true
        }
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

google_bigquery_dataset.dataset: Creating...
google_storage_bucket.data-lake-bucket: Creating...
google_bigquery_dataset.dataset: Creation complete after 1s [id=projects/<omitted>/datasets/trips_data_all]
google_storage_bucket.data-lake-bucket: Creation complete after 2s [id=dtc_data_lake_<omitted>]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

## Prepare Postgres 

Run Postgres and load data as shown in the videos

>Command:
```bash
# from the working directory where docker-compose.yaml is
docker-compose up
```

We'll use the yellow taxi trips from January 2021:

```bash
wget https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2021-01.csv
```

You will also need the dataset with zones:

```bash 
wget https://s3.amazonaws.com/nyc-tlc/misc/taxi+_zone_lookup.csv
```

>Command:
```bash
# Create a new ingest script that ingests both files called ingest_data.py, then dockerize it with
docker build -t taxi_ingest:homework .

# Now find the network where the docker-compose containers are running with
docker network ls

# Finally, run the dockerized script
docker run -it \
    --network=1_intro_default \
    taxi_ingest:homework \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table_name_1=trips \
    --table_name_2=zones
```

Download this data and put it to Postgres

## Question 3. Count records 

How many taxi trips were there on January 15?

Consider only trips that started on January 15.

>Command:
```sql
SELECT
  COUNT(1)
FROM
  trips
WHERE
  (tpep_pickup_datetime>='2021-01-15 00:00:00' AND
  tpep_pickup_datetime<'2021-01-16 00:00:00');
```
>Anwer (correct):
```
53024
```
>Proposed command for solution:
```sql
select count(*)
from trips
where tpep_pickup_datetime::date = '2021-01-15'
```

## Question 4. Average

Find the largest tip for each day. 
On which day it was the largest tip in January?

Use the pick up time for your calculations.

(note: it's not a typo, it's "tip", not "trip")

>Command:
```sql
SELECT
  CAST(tpep_pickup_datetime AS DATE) as "day",
  MAX(tip_amount) as "max_tip"
FROM
  trips
GROUP BY
  1
ORDER BY
  "max_tip" DESC;
```
>Answer (correct):
```
2021-01-20

The tip was 1140.44
```
>Proposed command for solution:
```sql
select date_trunc('day', tpep_pickup_datetime) as pickup_day,
  max(tip_amount) as max_tip
from trips
group by pickup_day
order by max_tip desc
limit 1;
```

## Question 5. Most popular destination

What was the most popular destination for passengers picked up 
in central park on January 14?

Use the pick up time for your calculations.

Enter the zone name (not id). If the zone name is unknown (missing), write "Unknown" 

>Command:
```sql
SELECT
    CONCAT(zpu."Borough", '/', zpu."Zone") AS "pickup_loc",
    CONCAT(zdo."Borough", '/', zdo."Zone") AS "dropoff_loc",
    COUNT(1) AS "amount_of_trips"
FROM
    trips t JOIN zones zpu
        ON t."PULocationID" = zpu."LocationID"
    JOIN zones zdo
        ON t."DOLocationID" = zdo."LocationID"
WHERE
	t."PULocationID" = (
		SELECT
			"LocationID"
		FROM
			zones zpu
		WHERE
			zpu."Zone" IN ('Central Park')
  )
GROUP BY
	1, 2 
ORDER BY
	"amount_of_trips" DESC
;
```
>Answer (**incorrect!**):
```
Upper East Side North
total trips: 2234
```
>Proposed command for solution:
```sql
select coalesce(dozones.zone,'Unknown') as zone,
count(*) as cant_trips
from trips as taxi
  inner join zones.taxi_zone_lookup as puzones
    on taxi.pulocationid = puzones.locationid
  left join zones.taxi_zone_lookup as dozones
    on taxi.dolocationid = dozones.locationid
where puzones.zone ilike '%central park%'
  and tpep_pickup_datetime::date = '2021-01-14'
group by 1
order by cant_trips desc
limit 1;
```
>Actual answer:
```
Upper East Side South
```

## Question 6. 

What's the pickup-dropoff pair with the largest 
average price for a ride (calculated based on `total_amount`)?

Enter two zone names separated by a slash

For example:

"Jamaica Bay / Clinton East"

If any of the zone names are unknown (missing), write "Unknown". For example, "Unknown / Clinton East". 

>Command:
```sql
SELECT
    CONCAT(zpu."Zone", '/', zdo."Zone") AS "zone_pair",
    AVG(t."total_amount") AS "total_amount_average"
FROM
    trips t JOIN zones zpu
        ON t."PULocationID" = zpu."LocationID"
    JOIN zones zdo
        ON t."DOLocationID" = zdo."LocationID"
GROUP BY
	1
ORDER BY
	2 DESC
;
```
>Answer (correct):
```
Alphabet City/Unknown
with an average price of 2292.4
```
>Proposed command for solution:
```sql
select concat(coalesce(puzones.zone,'Unknown'), '/', coalesce(dozones.zone,'Unknown')) as pickup_dropoff,
  avg(total_amount) as avg_price_ride
from trips as taxi
  left join zones as puzones
    on taxi.pulocationid = puzones.locationid
  left join zones as dozones
    on taxi.dolocationid = dozones.locationid
group by 1
order by avg_price_ride desc
limit 1;
```


## Submitting the solutions

* Form for submitting: https://forms.gle/yGQrkgRdVbiFs8Vd7
* You can submit your homework multiple times. In this case, only the last submission will be used. 

Deadline: 24 January, 17:00 CET

