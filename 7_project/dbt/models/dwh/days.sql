{{
    config(materialized='table',
        partition_by={
            "field": "created_at",
            "data_type": "timestamp",
            "granularity": "day"
        }
    )
}}

SELECT *
FROM {{ source('gh_archive_all', 'gh_external_table') }}