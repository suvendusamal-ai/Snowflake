select
    recognition_event_id,
    order_id,
    order_line_id,
    customer_id,
    region,
    recognition_type,
    recognition_date,
    year(recognition_date) as calendar_year,
    'Q' || quarter(recognition_date) as calendar_quarter,
    date_trunc('quarter', recognition_date)::date as quarter_start_date,
    amount,
    currency,
    source_system,
    source_relation,
    ingestion_timestamp
from {{ ref('stg_revenue_recognition_events') }}
