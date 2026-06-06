select
    customer_id,
    customer_name,
    customer_segment,
    min(order_date) as first_order_date,
    max(order_date) as most_recent_order_date,
    count(
        distinct case
            when order_status <> 'CANCELLED' then order_id
        end
    ) as valid_order_count,
    sum(
        case
            when order_status <> 'CANCELLED'
                then net_line_amount_usd
            else 0
        end
    ) as lifetime_revenue_usd
from {{ ref('int_order_lines_enriched') }}
group by
    customer_id,
    customer_name,
    customer_segment