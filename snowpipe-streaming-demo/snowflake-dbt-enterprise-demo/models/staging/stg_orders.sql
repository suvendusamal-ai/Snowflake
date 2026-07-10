select
    order_id,
    customer_id,
    order_date,
    upper(trim(status)) as order_status,
    upper(trim(currency_code)) as currency_code,
    updated_at,
    ingested_at
from {{ source('raw', 'orders') }}