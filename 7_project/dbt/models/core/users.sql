{{ config(materialized='table', schema='core') }}

select
    actor_id,
    actor_login,
    count(*) as commit_count
from {{ ref('stg_commits') }}
group by actor_id, actor_login