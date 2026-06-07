with facts as (
    select * from {{ ref('fct_order_items') }}
),

targets as (
    select * from {{ ref('segment_targets') }}
),

aggregated as (
    select
        customer_segment,
        count(distinct order_id) as completed_orders,
        sum(line_revenue) as revenue
    from facts
    group by 1
)

select
    aggregated.customer_segment,
    aggregated.completed_orders,
    aggregated.revenue,
    targets.target_revenue,
    {{ safe_divide('aggregated.revenue', 'targets.target_revenue') }} as target_attainment_ratio
from aggregated
left join targets
  on aggregated.customer_segment = targets.customer_segment
