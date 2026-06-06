with customers as (
    select * from {{ ref('stg_customers') }}
),
order_summary as (
    select * from {{ ref('int_customer_order_summary') }}
)
select
    customers.customer_id,
    customers.customer_name,
    customers.email,
    customers.customer_segment,
    customers.customer_status,
    customers.created_at,
    order_summary.first_order_date,
    order_summary.most_recent_order_date,
    coalesce(order_summary.valid_order_count, 0)
        as valid_order_count,
    coalesce(order_summary.lifetime_revenue_usd, 0)
        as lifetime_revenue_usd,
    case
        when coalesce(order_summary.lifetime_revenue_usd, 0)
            >= {{ var('high_value_order_threshold') }}
        then true
        else false
    end as high_value_customer_flag
from customers
left join order_summary
    on customers.customer_id = order_summary.customer_id