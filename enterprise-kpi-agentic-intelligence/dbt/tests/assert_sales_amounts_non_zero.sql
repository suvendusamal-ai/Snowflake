select event_id
from {{ ref('stg_sales_order_events') }}
where amount = 0
