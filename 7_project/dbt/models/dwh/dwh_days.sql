{{
    config(materialized='table',
        partition_by={
            "field": "created_at",
            "data_type": "timestamp",
            "granularity": "day"
        },
        cluster_by = "actor_id",
        schema='dwh'
    )
}}

SELECT *
FROM {{ source('dwh', 'gh_external_table') }}