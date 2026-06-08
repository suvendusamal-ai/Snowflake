select
    concat(order_id, '-', line_number) as order_item_key,
    order_id,
    line_number,
    product_name,
    quantity,
    unit_price,
    quantity * unit_price as line_revenue,
    updated_at,
    ingested_at
from {{ source('raw', 'order_items') }}
