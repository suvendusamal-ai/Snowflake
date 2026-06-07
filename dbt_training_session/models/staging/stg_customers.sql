select
    customer_id,
    customer_name,
    segment as customer_segment,
    upper(status) as customer_status,
    created_at,
    updated_at,
    ingested_at
from {{ source('raw', 'customers') }}
