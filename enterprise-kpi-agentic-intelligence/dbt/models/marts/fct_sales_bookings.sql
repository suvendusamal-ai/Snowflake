select
    event_id,
    order_id,
    order_line_id,
    customer_id,
    region,
    event_type,
    event_date,
    year(event_date) as calendar_year,
    'Q' || quarter(event_date) as calendar_quarter,
    date_trunc('quarter', event_date)::date as quarter_start_date,
    amount,
    currency,
    source_system,
    source_relation,
    ingestion_timestamp
from {{ ref('stg_sales_order_events') }}
