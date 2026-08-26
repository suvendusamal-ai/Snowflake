with staging as (
    select event_id, count(*) as staging_count
    from {{ ref('stg_sales_order_events') }}
    group by event_id
),
trusted as (
    select event_id, count(*) as trusted_count
    from {{ ref('fct_sales_bookings') }}
    group by event_id
)
select
    coalesce(staging.event_id, trusted.event_id) as event_id,
    coalesce(staging.staging_count, 0) as staging_count,
    coalesce(trusted.trusted_count, 0) as trusted_count
from staging
full outer join trusted using (event_id)
where coalesce(staging.staging_count, 0) <> 1
   or coalesce(trusted.trusted_count, 0) <> 1
