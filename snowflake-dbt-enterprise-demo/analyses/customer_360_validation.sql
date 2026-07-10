select
    customer_id,
    customer_name,
    customer_segment,
    customer_status,
    valid_order_count,
    lifetime_revenue_usd,
    high_value_customer_flag
from {{ ref('dim_customers') }}
order by lifetime_revenue_usd desc