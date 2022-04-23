{{ config(materialized='view', schema='staging') }}

select * from {{ source('staging', 'dwh_days')}}
where type = 'PushEvent'