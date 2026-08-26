with actual as (
    select
        count_if(event_id = 'SE003' and event_type = 'BOOKING' and amount = 800) as booking_count,
        count_if(event_id = 'SE004' and event_type = 'CANCELLATION' and amount = -800) as cancellation_count,
        count(*) as sales_event_count
    from {{ ref('fct_sales_bookings') }}
    where order_id = 'O300'
),
recognition as (
    select count(*) as recognition_event_count
    from {{ ref('fct_recognized_revenue') }}
    where order_id = 'O300'
)
select actual.*, recognition.recognition_event_count
from actual cross join recognition
where actual.booking_count <> 1
   or actual.cancellation_count <> 1
   or actual.sales_event_count <> 2
   or recognition.recognition_event_count <> 0
