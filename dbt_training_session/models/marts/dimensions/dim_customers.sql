with customers as (
    select * from {{ ref('stg_customers') }}
),

facts as (
    select * from {{ ref('fct_order_items') }}
),

aggregated as (
    select
        customer_id,
        min(order_date) as first_order_date,
        max(order_date) as most_recent_order_date,
        count(distinct order_id) as completed_order_count,
        sum(line_revenue) as lifetime_revenue
    from facts
    group by 1
)

select
    customers.customer_id,
    customers.customer_name,
    customers.customer_segment,
    customers.customer_status,
    customers.created_at,
    aggregated.first_order_date,
    aggregated.most_recent_order_date,
    coalesce(aggregated.completed_order_count, 0) as completed_order_count,
    coalesce(aggregated.lifetime_revenue, 0) as lifetime_revenue,
    coalesce(aggregated.lifetime_revenue, 0) >= {{ var('high_value_customer_threshold') }} as high_value_customer_flag
from customers
left join aggregated using (customer_id)
