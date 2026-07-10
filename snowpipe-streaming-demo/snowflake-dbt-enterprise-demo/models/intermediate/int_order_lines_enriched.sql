with order_items as (
    select * from {{ ref('stg_order_items') }}
),
orders as (
    select * from {{ ref('stg_orders') }}
),
customers as (
    select * from {{ ref('stg_customers') }}
),
products as (
    select * from {{ ref('stg_products') }}
),
currency_rates as (
    select * from {{ ref('currency_rates') }}
)
select
    concat(order_items.order_id, '-', order_items.line_number)
        as order_item_key,
    order_items.order_id,
    order_items.line_number,
    orders.order_date,
    orders.order_status,
    orders.currency_code,
    customers.customer_id,
    customers.customer_name,
    customers.customer_segment,
    products.product_id,
    products.product_name,
    products.product_category,
    order_items.quantity,
    order_items.unit_price,
    order_items.discount_pct,
    order_items.gross_line_amount,
    order_items.net_line_amount,
    currency_rates.rate_to_usd,
    order_items.net_line_amount * currency_rates.rate_to_usd
        as net_line_amount_usd,
    greatest(order_items.updated_at, orders.updated_at)
        as source_updated_at
from order_items
inner join orders
    on order_items.order_id = orders.order_id
inner join customers
    on orders.customer_id = customers.customer_id
inner join products
    on order_items.product_id = products.product_id
inner join currency_rates
    on orders.currency_code = currency_rates.currency_code