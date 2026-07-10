with customer_totals as (
    select
        customer_id,
        lifetime_revenue
    from {{ ref('dim_customers') }}
),

fact_totals as (
    select
        customer_id,
        sum(line_revenue) as fact_revenue
    from {{ ref('fct_order_items') }}
    group by 1
)

select
    customer_totals.customer_id,
    customer_totals.lifetime_revenue,
    fact_totals.fact_revenue
from customer_totals
inner join fact_totals using (customer_id)
where abs(customer_totals.lifetime_revenue - fact_totals.fact_revenue) > 0.01
