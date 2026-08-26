with expected as (
    select '2025_Q1' as period_name, 1800::number(18, 2) as expected_amount
    union all select '2025_Q2', 4000::number(18, 2)
    union all select '2025_H1', 5800::number(18, 2)
),
actual as (
    select '2025_Q1' as period_name, coalesce(sum(amount), 0) as actual_amount
    from {{ ref('fct_recognized_revenue') }}
    where recognition_date >= '2025-01-01'::date and recognition_date < '2025-04-01'::date
    union all
    select '2025_Q2', coalesce(sum(amount), 0)
    from {{ ref('fct_recognized_revenue') }}
    where recognition_date >= '2025-04-01'::date and recognition_date < '2025-07-01'::date
    union all
    select '2025_H1', coalesce(sum(amount), 0)
    from {{ ref('fct_recognized_revenue') }}
    where recognition_date >= '2025-01-01'::date and recognition_date < '2025-07-01'::date
)
select expected.period_name, expected.expected_amount, actual.actual_amount
from expected
join actual using (period_name)
where expected.expected_amount <> actual.actual_amount
