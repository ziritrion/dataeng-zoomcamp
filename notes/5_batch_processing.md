# Introduction to Batch Processing

## Batch vs Streaming

There are 2 ways of processing data:
* ***Batch processing***: processing _chunks_ of data at _regular intervals_.
    * Example: processing taxi trips each month.
        ```mermaid
        graph LR;
            a[(taxi trips DB)]-->b(batch job)
            b-->a
        ```
* ***Streaming***: processing data _on the fly_.
    * Example: processing a taxi trip as soon as it's generated.
        ```mermaid
        graph LR;
            a{{User}}-. gets on taxi .->b{{taxi}}
            b-- ride start event -->c([data stream])
            c-->d(Processor)
            d-->e([data stream])
        ```

This lesson will cover ***batch processing***. Next lesson will cover streaming.

## Types of batch jobs

A ***batch job*** is a ***job*** (a unit of work) that will process data in batches.

Batch jobs may be _scheduled_ in many ways:

* Weekly
* Daily (very common)
* Hourly (very common)
* X timnes per hous
* Every 5 minutes
* Etc...

Batch jobs may also be carried out using different technologies:

* Python scripts (like the [data pipelines in lesson 1](1_intro.md#creating-a-custom-pipeline-with-docker)).
    * Python scripts can be run anywhere (Kubernets, AWS Batch, ...)
* SQL (like the [dbt models in lesson 4](4_analytics.md#developing-with-dbt)).
* Spark (what we will use for this lesson)
* Flink
* Etc...

## Orchestrating batch jobs

Batch jobs are commonly orchestrated with tools such as [Airflow](2_data_ingestion.md#airflow-architecture).

A common workflow for batch jobs may be the following:

```mermaid
  graph LR;
      A(DataLake CSV)-->B(Python);
      B-->C[(SQL-dbt)]
      C-->D(Spark)
      D-->E(Python)
```

## Pros and cons of batch jobs

* Advantages:
    * Easy to manage. There are multiple tools to manage them (the technologies we already mentioned)
    * Re-executable. Jobs can be easily retried if they fail.
    * Scalable. Scripts can be executed in more capable machines; Spark can be run in bigger clusters, etc.
* Disadvantages:
    * Delay. Each task of the workflow in the previous section may take a few minutes; assuming the whole workflow takes 20 minutes, we would need to wait those 20 minutes until the data is ready for work.

However, the advantages of batch jobs often compensate for its shortcomings, and as a result most companies that deal with data tend to work with batch jobs mos of the time (probably 90%).


# Introduction to Spark

## What is Spark?

[Apache Spark](https://spark.apache.org/) is an open-source ***multi-language*** unified analytics ***engine*** for large-scale data processing.

Spark is an ***engine*** because it _processes data_.

```mermaid
graph LR;
    A[(Data Lake)]-->|Pulls data|B(Spark)
    B-->|Does something to data|B
    B-->|Outputs data|A
```

Spark can be ran in _clusters_ with multiple _nodes_, each pulling and transforming data.

Spark is ***multi-language*** because we can use Java and Scala natively, and there are wrappers for Python, R and other languages.

The wrapper for Python is called [PySpark](https://spark.apache.org/docs/latest/api/python/).

Spark can deal with both batches and streaming data. The technique for streaming data is seeing a stream of data as a sequence of small batches and then applying similar techniques on them to those used on regular badges. We will cover streaming in detail in the next lesson.

# Why do we need Spark?

Spark is used for transforming data in a Data Lake.

There are tools such as Hive, Presto or Athena (a AWS managed Presto) that allow you to express jobs as SQL queries. However, there are times where you need to apply more complex manipulation which are very difficult or even impossible to express with SQL (such as ML models); in those instances, Spark is the tool to use.

```mermaid
graph LR;
    A[(Data Lake)]-->B{Can the <br /> job be expressed <br /> with SQL?}
    B-->|Yes|C(Hive/Presto/Athena)
    B-->|No|D(Spark)
    C & D -->E[(Data Lake)]
```

A typical workflow may combine both tools. Here's an example of a workflow involving Machine Learning:

```mermaid
graph LR;
    A((Raw data))-->B[(Data Lake)]
    B-->C(SQL Athena job)
    C-->D(Spark job)
    D-->|Train a model|E(Python job <br /> Train ML)
    D-->|Use a model|F(Spark job <br /> Apply model)
    E-->G([Model])
    G-->F
    F-->|Save output|B
```

In this scenario, most of the preprocessing would be happening in Athena, so for everything that can be expressed with SQL, it's always a good idea to do so, but for everything else, there's Spark.

___


# Installing Spark

## Connecting to an instance on GCP and installing it there.

# First look at Spark/PySpark

## Reading CSV files
## Partitions
## Saving data to Parquet for local experiments
## Spark master UI

# Spark DataFrames
## Actions vs Transformations
## Partitions
## Functions and UDFs

# Spark SQL
## Temporary tables
## Some simple queries from week 4

# Joins in Spark
## merge sort join
## broadcasting

# RDDs
## From DF to RDD
## map
## reduce
## mapPartition
## From RDD to DF

# Spark internals
## driver, master and executors
## partitioning + coalesce
## shuffling
## group by or notg group by?
## broadcasting

# Spark and Docker

# Running Spark in the Cloud (GCP)

# Connecting Spark to a DWH
## Spark with BigQuery (Athena/presto/hive/etc - similar)
## reading from GCP and saving to BG