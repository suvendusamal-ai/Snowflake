select
    recognition_event_id,
    order_id,
    order_line_id,
    customer_id,
    region,
    recognition_type,
    recognition_date,
    amount,
    currency,
    source_system,
    '{{ source("raw", "revenue_recognition_events") }}' as source_relation,
    ingestion_timestamp
from {{ source('raw', 'revenue_recognition_events') }}
