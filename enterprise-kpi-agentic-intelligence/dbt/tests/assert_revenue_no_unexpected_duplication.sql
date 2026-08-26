with staging as (
    select recognition_event_id, count(*) as staging_count
    from {{ ref('stg_revenue_recognition_events') }}
    group by recognition_event_id
),
trusted as (
    select recognition_event_id, count(*) as trusted_count
    from {{ ref('fct_recognized_revenue') }}
    group by recognition_event_id
)
select
    coalesce(staging.recognition_event_id, trusted.recognition_event_id) as recognition_event_id,
    coalesce(staging.staging_count, 0) as staging_count,
    coalesce(trusted.trusted_count, 0) as trusted_count
from staging
full outer join trusted using (recognition_event_id)
where coalesce(staging.staging_count, 0) <> 1
   or coalesce(trusted.trusted_count, 0) <> 1
