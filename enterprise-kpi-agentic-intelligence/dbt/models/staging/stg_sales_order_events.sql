select
    event_id,
    order_id,
    order_line_id,
    customer_id,
    region,
    event_type,
    event_date,
    amount,
    currency,
    source_system,
    '{{ source("raw", "sales_order_events") }}' as source_relation,
    ingestion_timestamp
from {{ source('raw', 'sales_order_events') }}
