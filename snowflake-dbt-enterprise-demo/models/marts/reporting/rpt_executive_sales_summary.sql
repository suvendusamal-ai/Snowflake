with valid_orders as (

    select *
    from {{ ref('fct_order_items') }}
    where order_status <> 'CANCELLED'

),

monthly as (

    select
        date_trunc('month', order_date)::date as revenue_month,
        count(distinct order_id) as order_count,
        count(distinct customer_id) as active_customer_count,
        sum(net_line_amount_usd) as revenue_usd
    from valid_orders
    group by revenue_month

)

select
    revenue_month,
    order_count,
    active_customer_count,
    revenue_usd,
    revenue_usd / nullif(order_count, 0)
        as average_order_value_usd,
    lag(revenue_usd) over (
        order by revenue_month
    ) as prior_month_revenue_usd,
    revenue_usd - lag(revenue_usd) over (
        order by revenue_month
    ) as revenue_change_usd
from monthly