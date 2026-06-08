-- Analyses compile but are not materialized.
select
    customer_id,
    customer_name,
    customer_segment,
    lifetime_revenue,
    high_value_customer_flag
from {{ ref('dim_customers') }}
order by lifetime_revenue desc
