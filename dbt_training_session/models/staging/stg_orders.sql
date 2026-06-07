select
    order_id,
    customer_id,
    order_date,
    upper(status) as order_status,
    updated_at,
    ingested_at
from {{ source('raw', 'orders') }}
