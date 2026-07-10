with fact_total as (

    select sum(net_line_amount) as amount
    from {{ ref('fct_order_items') }}

),

staging_total as (

    select sum(net_line_amount) as amount
    from {{ ref('stg_order_items') }}

)

select
    fact_total.amount as fact_amount,
    staging_total.amount as staging_amount
from fact_total
cross join staging_total
where abs(fact_total.amount - staging_total.amount) > 0.01