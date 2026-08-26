select
    count_if(
        recognition_type = 'PARTIAL'
        and recognition_date >= '2025-01-01'::date
        and recognition_date < '2025-04-01'::date
        and amount = 800
    ) as q1_partial_count,
    count_if(
        recognition_type = 'FINAL'
        and recognition_date >= '2025-04-01'::date
        and recognition_date < '2025-07-01'::date
        and amount = 1200
    ) as q2_final_count,
    count(*) as recognition_event_count
from {{ ref('fct_recognized_revenue') }}
where order_id = 'O400'
having q1_partial_count <> 1
    or q2_final_count <> 1
    or recognition_event_count <> 2
