{{ config(materialized='view', schema='staging') }}

select * from {{ ref('dwh_days') }}
where type = 'PushEvent'