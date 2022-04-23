{{ config(materialized='view') }}

select * from {{ source('staging', 'dwh_days')}}
where 'type' = 'PushEvent'