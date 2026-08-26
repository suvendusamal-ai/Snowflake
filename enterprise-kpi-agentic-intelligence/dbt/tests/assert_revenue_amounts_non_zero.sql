select recognition_event_id
from {{ ref('stg_revenue_recognition_events') }}
where amount = 0
