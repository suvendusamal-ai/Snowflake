with actuals as (

    select
        customer_segment as segment,
        sum(lifetime_revenue_usd) as actual_revenue_usd,
        count(*) as customer_count
    from {{ ref('dim_customers') }}
    group by customer_segment

),

targets as (

    select *
    from {{ ref('segment_targets') }}

)

select
    actuals.segment,
    actuals.customer_count,
    actuals.actual_revenue_usd,
    targets.annual_revenue_target_usd,
    actuals.actual_revenue_usd
        / nullif(targets.annual_revenue_target_usd, 0)
        as target_attainment_ratio
from actuals
inner join targets
    on actuals.segment = targets.segment