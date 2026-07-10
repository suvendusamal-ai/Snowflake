with orders as (
    select * from {{ ref('stg_orders') }}
),

order_items as (
    select * from {{ ref('stg_order_items') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

joined as (
    select
        order_items.order_item_key,
        order_items.order_id,
        order_items.line_number,
        order_items.product_name,
        order_items.quantity,
        order_items.unit_price,
        order_items.line_revenue,
        orders.order_date,
        orders.order_status,
        customers.customer_id,
        customers.customer_name,
        customers.customer_segment,
        greatest(order_items.updated_at, orders.updated_at, customers.updated_at) as source_updated_at
    from order_items
    inner join orders using (order_id)
    inner join customers using (customer_id)
)

select * from joined
