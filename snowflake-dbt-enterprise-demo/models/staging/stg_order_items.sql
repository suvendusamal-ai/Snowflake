select
    order_id,
    line_number,
    product_id,
    quantity,
    unit_price,
    coalesce(discount_pct, 0) as discount_pct,
    quantity * unit_price as gross_line_amount,
    quantity * unit_price
        * (1 - coalesce(discount_pct, 0) / 100) as net_line_amount,
    updated_at,
    ingested_at
from {{ source('raw', 'order_items') }}